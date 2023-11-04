"""Nautobot SSoT Citrix ADM Adapter for Citrix ADM SSoT plugin."""
from datetime import datetime
from django.conf import settings
from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from netutils.ip import netmask_to_cidr
from nautobot.dcim.models import Device, Interface
from nautobot.extras.models import Job
from nautobot.ipam.models import IPAddress
from nautobot_ssot_citrix_adm.constants import DEVICETYPE_MAP
from nautobot_ssot_citrix_adm.diffsync.models.citrix_adm import (
    CitrixAdmDatacenter,
    CitrixAdmDevice,
    CitrixAdmPort,
    CitrixAdmAddress,
)
from nautobot_ssot_citrix_adm.utils.citrix_adm import parse_hostname_for_role, parse_version, CitrixNitroClient

PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_ssot_citrix_adm"]


class LabelMixin:
    """Add labels onto Nautobot objects to provide information on sync status with Citrix ADM."""

    def label_imported_objects(self, target):
        """Add CustomFields to all objects that were successfully synced to the target."""
        for modelname in ["device", "port", "address"]:
            for local_instance in self.get_all(modelname):
                unique_id = local_instance.get_unique_id()
                # Verify that the object now has a counterpart in the target DiffSync
                try:
                    target.get(modelname, unique_id)
                except ObjectNotFound:
                    continue

                self.label_object(modelname, unique_id)

    def label_object(self, modelname, unique_id):
        """Apply the given CustomField to the identified object."""

        def _label_object(nautobot_object):
            """Apply custom field to object, if applicable."""
            nautobot_object.custom_field_data["ssot_last_synchronized"] = today
            nautobot_object.custom_field_data["system_of_record"] = "Citrix ADM"
            nautobot_object.validated_save()

        today = datetime.today().date().isoformat()
        model_instance, name, device, port, address = None, None, None, None, None
        try:
            model_instance = self.get(modelname, unique_id)
        except ObjectNotFound:
            ids = unique_id.split("__")
            if modelname == "address":
                address = ids[0]
                device = ids[1]
                port = ids[2]
            elif modelname == "device":
                name = unique_id
            elif modelname == "port":
                name = ids[0]
                device = ids[1]

        if model_instance:
            if hasattr(model_instance, "name"):
                name = model_instance.name
            if hasattr(model_instance, "device"):
                device = model_instance.device
            if hasattr(model_instance, "port"):
                port = model_instance.port
            if hasattr(model_instance, "address"):
                address = model_instance.address

        if modelname == "device" and name:
            _label_object(Device.objects.get(name=name))
        elif modelname == "port" and (name and device):
            _label_object(Interface.objects.get(name=name, device__name=device))
        elif modelname == "address" and (address and device and port):
            _label_object(
                IPAddress.objects.get(
                    address=address,
                    interface=Interface.objects.get(device__name=device, name=port),
                )
            )


class CitrixAdmAdapter(DiffSync, LabelMixin):
    """DiffSync adapter for Citrix ADM."""

    datacenter = CitrixAdmDatacenter
    device = CitrixAdmDevice
    address = CitrixAdmAddress
    port = CitrixAdmPort

    top_level = ["datacenter", "device", "address"]

    def __init__(self, *args, job: Job, sync=None, client: CitrixNitroClient, tenant: str = "", **kwargs):
        """Initialize Citrix ADM.

        Args:
            job (Job): Citrix ADM job.
            sync (object, optional): Citrix ADM DiffSync. Defaults to None.
            client (CitrixNitroClient): Citrix ADM API client connection object.
            tenant (str): Name of Tenant to associate Devices and IP Addresses with.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.conn = client
        self.tenant = tenant
        self.adm_site_map = {}
        self.adm_device_map = {}

    def create_site_map(self):
        """Create mapping of ADM Datacenters to information about the Datacenter."""
        sites = self.conn.get_sites()
        for site in sites:
            self.adm_site_map[site["id"]] = site

    def load_site(self, site_info: dict):
        """Load sites from Citrix ADM into DiffSync models.

        Args:
            site_info (dict): Dictionary containing information about Datacenter to be imported.
        """
        try:
            found_site = self.get(self.datacenter, {"name": site_info.get("name"), "region": site_info.get("region")})
            if found_site:
                self.job.log_warning(message=f"Duplicate Site attempting to be loaded: {site_info}.")
        except ObjectNotFound:
            if self.job.kwargs.get("debug"):
                self.job.log_info(message=f"Attempting to load DC: {site_info['name']}")
            new_site = self.datacenter(
                name=site_info["name"],
                region=site_info["region"],
                latitude=site_info["latitude"][:9].rstrip("0") if site_info.get("latitude") else "",
                longitude=site_info["longitude"][:9].rstrip("0") if site_info.get("longitude") else "",
                uuid=None,
            )
            self.add(new_site)

    def load_devices(self):
        """Load devices from Citrix ADM into DiffSync models."""
        devices = self.conn.get_devices()
        for dev in devices:
            if not dev.get("hostname"):
                self.job.log_warning(message=f"Device without hostname will not be loaded. {dev}")
                continue
            try:
                found_dev = self.get(self.device, dev["hostname"])
                if found_dev:
                    self.job.log_warning(message=f"Duplicate Device attempting to be loaded: {dev['hostname']}")
            except ObjectNotFound:
                site = self.adm_site_map[dev["datacenter_id"]]
                self.load_site(site_info=site)
                role = parse_hostname_for_role(
                    hostname_map=PLUGIN_CFG.get("hostname_mapping"), device_hostname=dev["hostname"]
                )
                new_dev = self.device(
                    name=dev["hostname"],
                    model=DEVICETYPE_MAP[dev["type"]] if dev["type"] in DEVICETYPE_MAP else dev["type"],
                    role=role,
                    serial=dev["serialnumber"],
                    site=site["name"],
                    status="Active" if dev["instance_state"] == "Up" else "Offline",
                    tenant=self.tenant,
                    version=parse_version(dev["version"]),
                    uuid=None,
                )
                self.add(new_dev)
                self.adm_device_map[dev["hostname"]] = dev
                if dev.get("mgmt_ip_address"):
                    address = f"{dev['mgmt_ip_address']}/{netmask_to_cidr(netmask=dev['netmask'])}"
                    try:
                        _ = self.get(self.port, {"name": "Management", "device": dev["hostname"], "port": "Management"})
                    except ObjectNotFound:
                        mgmt_port = self.add_port(dev_name=dev["hostname"])
                        new_dev.add_child(mgmt_port)
                        try:
                            _ = self.get(
                                self.address,
                                {"address": address, "device": dev["hostname"], "port": "Management"},
                            )
                        except ObjectNotFound:
                            self.load_address(address=address, device=dev["hostname"], port="Management", primary=True)

    def create_port_map(self):
        """Create a port/vlan/ip map for each ADC instance."""
        self.job.log_info(message=f"Retrieving nsip and port bindings from ADC instances.")
        for _, adc in self.adm_device_map.items():
            nsip6s = self.conn.get_nsip6(adc)
            vlan_bindings = self.conn.get_vlan_bindings(adc)
            ports = []

            try:
                for binding in vlan_bindings:
                    if binding.get("vlan_nsip_binding"):
                        for nsip in binding["vlan_nsip_binding"]:
                            vlan = nsip["id"]
                            ipaddress = nsip["ipaddress"]
                            netmask = netmask_to_cidr(nsip["netmask"])
                            port = binding["vlan_interface_binding"][0]["ifnum"]
                            record = {"vlan": vlan, "ipaddress": ipaddress, "netmask": netmask, "port": port}
                            ports.append(record)
                    if binding.get("vlan_nsip6_binding"):
                        for nsip6 in binding["vlan_nsip6_binding"]:
                            vlan = nsip6["id"]
                            ipaddress, netmask = nsip6["ipaddress"].split("/")
                            port = binding["vlan_interface_binding"][0]["ifnum"]
                            record = {"vlan": vlan, "ipaddress": ipaddress, "netmask": netmask, "port": port}
                            ports.append(record)
            except KeyError:
                self.job.log_warning(message=f"Unable to load bindings for {adc['hostname']}.")

            try:
                for nsip6 in nsip6s:
                    if nsip6["scope"] == "link-local":
                        vlan = nsip6["vlan"]
                        ipaddress, netmask = nsip6["ipv6address"].split("/")
                        port = "L0/1"
                        record = {"vlan": vlan, "ipaddress": ipaddress, "netmask": netmask, "port": port}
                        ports.append(record)
            except KeyError:
                self.job.log_warning(message=f"Unable to load nsip6 for {adc['hostname']}.")

            self.adm_device_map[adc["hostname"]]["ports"] = ports

    def load_ports(self):
        """Load ports from Citrix ADM into DiffSync models."""
        for _, adc in self.adm_device_map.items():
            for port in adc["ports"]:
                try:
                    self.get(self.port, {"name": port["port"], "device": adc["hostname"]})
                except ObjectNotFound:
                    dev = self.get(self.device, adc["hostname"])
                    new_port = self.add_port(
                        dev_name=adc["hostname"],
                        port_name=port["port"],
                        port_status="ENABLED",
                        description="",
                    )
                    dev.add_child(new_port)

    def load_addresses(self):
        """Load addresses from Citrix ADC instances into Diffsync models."""
        for _, adc in self.adm_device_map.items():
            for port in adc["ports"]:
                if port.get("ipaddress"):
                    try:
                        self.get(
                            self.address,
                            {
                                "address": f"{port['ipaddress']}/{port['netmask']}",
                                "device": adc["hostname"],
                                "port": port["port"],
                            },
                        )
                    except ObjectNotFound:
                        self.load_address(
                            address=f"{port['ipaddress']}/{port['netmask']}",
                            device=adc["hostname"],
                            port=port["port"],
                        )

    def add_port(
        self, dev_name: str, port_name: str = "Management", port_status: str = "ENABLED", description: str = ""
    ):
        """Method to add Port DiffSync model.

        Args:
            dev_name (str): Name of device port is attached to.
            port_name (str, optional): Name of port to create. Defaults to "Management".
            port_status (str, optional): Status of port to create. Defaults to "ENABLED".
            description (str, optional): Description for port. Defaults to "".

        Returns:
            CitrixAdmPort: DiffSync model for Port that was loaded.
        """
        new_port = self.port(
            name=port_name,
            device=dev_name,
            status="Active" if port_status == "ENABLED" else "Offline",
            description=description,
            uuid=None,
        )
        self.add(new_port)
        return new_port

    def load_address(self, address: str, device: str, port: str, primary: bool = False):
        """Load CitrixAdmAddress DiffSync model with specified data.

        Args:
            address (str): IP Address to be loaded.
            device (str): Device that IP resides on.
            port (str): Interface that IP is configured on.
            primary (str): Whether the IP is primary IP for assigned device. Defaults to False.
        """
        new_addr = self.address(
            address=address,
            device=device,
            port=port,
            primary=primary,
            tenant=self.tenant,
            uuid=None,
        )
        self.add(new_addr)

    def load(self):
        """Load data from Citrix ADM into DiffSync models."""
        self.create_site_map()
        self.load_devices()
        self.create_port_map()
        self.load_ports()
        self.load_addresses()
