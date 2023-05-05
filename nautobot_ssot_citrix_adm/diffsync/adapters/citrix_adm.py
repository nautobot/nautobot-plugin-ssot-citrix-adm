"""Nautobot SSoT Citrix ADM Adapter for Citrix ADM SSoT plugin."""
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from netutils.ip import netmask_to_cidr
from nautobot.dcim.models import Device, Interface
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField
from nautobot.ipam.models import IPAddress
from nautobot_ssot_citrix_adm.constants import DEVICETYPE_MAP
from nautobot_ssot_citrix_adm.diffsync.models.citrix_adm import (
    CitrixAdmDatacenter,
    CitrixAdmDevice,
    CitrixAdmPort,
    CitrixAdmAddress,
)
from nautobot_ssot_citrix_adm.utils.citrix_adm import parse_version, CitrixNitroClient


class LabelMixin:
    """Add labels onto Nautobot objects to provide information on sync status with Citrix ADM."""

    def label_imported_objects(self, target):
        """Add CustomFields to all objects that were successfully synced to the target."""
        # Ensure that the "ssot-last-synchronized" custom field is present; as above, it *should* already exist.
        cf_dict = {
            "type": CustomFieldTypeChoices.TYPE_DATE,
            "name": "ssot_last_synchronized",
            "slug": "ssot_last_synchronized",
            "label": "Last sync from System of Record",
        }
        custom_field, _ = CustomField.objects.get_or_create(name=cf_dict["name"], defaults=cf_dict)
        for model in [Device, Interface, IPAddress]:
            custom_field.content_types.add(ContentType.objects.get_for_model(model))

        for modelname in ["device", "port", "address"]:
            for local_instance in self.get_all(modelname):
                unique_id = local_instance.get_unique_id()
                # Verify that the object now has a counterpart in the target DiffSync
                try:
                    target.get(modelname, unique_id)
                except ObjectNotFound:
                    continue

                self.label_object(modelname, unique_id, custom_field)

    def label_object(self, modelname, unique_id, custom_field):
        """Apply the given CustomField to the identified object."""

        def _label_object(nautobot_object):
            """Apply custom field to object, if applicable."""
            nautobot_object.custom_field_data[custom_field.name] = today
            nautobot_object.custom_field_data["system_of_record"] = "Citrix ADM"
            nautobot_object.validated_save()

        today = datetime.now().today()
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

    def __init__(self, *args, job=None, sync=None, client: CitrixNitroClient, **kwargs):
        """Initialize Citrix ADM.

        Args:
            job (object, optional): Citrix ADM job. Defaults to None.
            sync (object, optional): Citrix ADM DiffSync. Defaults to None.
            client (CitrixNitroClient): Citrix ADM API client connection object.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.conn = client
        self.adm_site_map = {}
        self.adm_device_map = {}

    def load_sites(self):
        """Load sites from Citrix ADM into DiffSync models."""
        sites = self.conn.get_sites()
        for site in sites:
            if site.get("name") == "Default":
                self.job.log_info("Skipping loading of Default datacenter.")
                continue
            try:
                found_site = self.get(self.datacenter, {"name": site.get("name"), "region": site.get("region")})
                if found_site:
                    self.job.log_warning(message=f"Duplicate Site attempting to be loaded: {site}.")
            except ObjectNotFound:
                if self.job.kwargs.get("debug"):
                    self.job.log_info(message=f"Attempting to load DC: {site['name']} {site}")
                new_site = self.datacenter(
                    name=site["name"],
                    region=site["region"],
                    latitude=site["latitude"][:9].rstrip("0") if site.get("latitude") else "",
                    longitude=site["longitude"][:9].rstrip("0") if site.get("longitude") else "",
                    uuid=None,
                )
                self.add(new_site)
                self.adm_site_map[site["id"]] = site["name"]

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
                    self.job.log_warning(message=f"Duplicate Device attempting to be loaded: {dev}.")
            except ObjectNotFound:
                new_dev = self.device(
                    name=dev["hostname"],
                    model=DEVICETYPE_MAP[dev["type"]] if dev["type"] in DEVICETYPE_MAP else dev["type"],
                    serial=dev["serialnumber"],
                    site=self.adm_site_map[dev["datacenter_id"]],
                    status="Active" if dev["instance_state"] == "Up" else "Offline",
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

    def load_ports(self):
        """Load ports from Citrix ADM into DiffSync models."""
        ports = self.conn.get_ports()
        for port in ports:
            try:
                self.get(self.port, {"name": port["devicename"], "device": port["hostname"]})
                self.job.log_warning(
                    message=f"Duplicate port {port['devicename']} attempting to be loaded for {port['hostname']}."
                )
                continue
            except ObjectNotFound:
                try:
                    dev = self.get(self.device, port["hostname"])
                    new_port = self.add_port(
                        dev_name=port["hostname"],
                        port_name=port["devicename"],
                        port_status=port["state"],
                        description=port["description"],
                    )
                    dev.add_child(new_port)
                    if port.get("ns_ip_address"):
                        netmask = netmask_to_cidr(self.adm_device_map[port["hostname"]]["netmask"])
                        try:
                            # check if address already loaded on Management port
                            mgmt_addr = self.get(
                                self.address,
                                {
                                    "address": f"{port['ns_ip_address']}/{netmask}",
                                    "device": port["hostname"],
                                    "port": "Management",
                                },
                            )
                            self.job.log_info(
                                message=f"Management address {port['ns_ip_address']} found on {port['devicename']} so updating DiffSync models to use this port."
                            )
                            mgmt_addr.port = port["devicename"]
                            mgmt_port = self.get(self.port, {"name": "Management", "device": port["hostname"]})
                            mgmt_port.name = port["devicename"]
                        except ObjectNotFound:
                            self.load_address(
                                address=f"{port['ns_ip_address']}/{netmask}",
                                device=port["hostname"],
                                port=port["devicename"],
                            )
                except ObjectNotFound:
                    self.job.log_warning(
                        message=f"Unable to find device {port['hostname']} so skipping loading of port {port['devicename']}."
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
            uuid=None,
        )
        self.add(new_addr)

    def load(self):
        """Load data from Citrix ADM into DiffSync models."""
        self.load_sites()
        self.load_devices()
        self.load_ports()
