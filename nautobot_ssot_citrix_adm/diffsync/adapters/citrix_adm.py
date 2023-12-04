"""Nautobot SSoT Citrix ADM Adapter for Citrix ADM SSoT plugin."""
import ipaddress
from django.conf import settings
from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from nautobot.extras.models import Job
from nautobot_ssot_citrix_adm.constants import DEVICETYPE_MAP
from nautobot_ssot_citrix_adm.diffsync.models.citrix_adm import (
    CitrixAdmDatacenter,
    CitrixAdmDevice,
    CitrixAdmPort,
    CitrixAdmSubnet,
    CitrixAdmAddress,
)
from nautobot_ssot_citrix_adm.utils.citrix_adm import (
    parse_hostname_for_role,
    parse_version,
    CitrixNitroClient,
    parse_vlan_bindings,
    parse_nsips,
    parse_nsip6s,
)

PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_ssot_citrix_adm"]


class CitrixAdmAdapter(DiffSync):
    """DiffSync adapter for Citrix ADM."""

    datacenter = CitrixAdmDatacenter
    device = CitrixAdmDevice
    address = CitrixAdmAddress
    prefix = CitrixAdmSubnet
    port = CitrixAdmPort

    top_level = ["datacenter", "device", "prefix", "address"]

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
            if found_site and self.job.debug:
                self.job.logger.warning(f"Duplicate Site attempting to be loaded: {site_info}.")
        except ObjectNotFound:
            if self.job.debug:
                self.job.logger.info(f"Attempting to load DC: {site_info['name']}")
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
                self.job.logger.warning(f"Device without hostname will not be loaded. {dev}")
                continue
            try:
                found_dev = self.get(self.device, dev["hostname"])
                if found_dev:
                    self.job.logger.warning(f"Duplicate Device attempting to be loaded: {dev['hostname']}")
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
                    hanode=dev["ha_ip_address"],
                )
                self.add(new_dev)
                self.adm_device_map[dev["hostname"]] = dev

    def create_port_map(self):
        """Create a port/vlan/ip map for each ADC instance."""
        self.job.logger.info("Retrieving NSIP and port bindings from ADC instances.")
        for _, adc in self.adm_device_map.items():
            vlan_bindings = self.conn.get_vlan_bindings(adc)
            nsips = self.conn.get_nsip(adc)
            nsip6s = self.conn.get_nsip6(adc)

            ports = parse_vlan_bindings(vlan_bindings, adc, self.job)
            ports = parse_nsips(nsips, ports, adc)
            ports = parse_nsip6s(nsip6s, ports)

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
                    addr = f"{port['ipaddress']}/{port['netmask']}"
                    prefix = ipaddress.ip_interface(addr).network.with_prefixlen
                    self.load_prefix(prefix=prefix)
                    _tags = port["tags"] if port.get("tags") else []
                    if len(_tags) > 1:
                        _tags.sort()
                    _primary = True if "MGMT" in _tags or "MIP" in _tags else False
                    self.load_address(
                        address=addr,
                        prefix=prefix,
                        device=adc["hostname"],
                        port=port["port"],
                        tags=_tags,
                        primary=_primary,
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

    def load_prefix(self, prefix: str):
        """Load CitrixAdmSubnet DiffSync model with specified data.

        Args:
            prefix (str): Prefix to be loaded.
        """
        if self.tenant:
            namespace = self.tenant
        else:
            namespace = "Global"
        try:
            self.get(self.prefix, {"prefix": prefix, "namespace": namespace})
        except ObjectNotFound:
            new_pf = self.prefix(
                prefix=prefix,
                namespace=namespace,
                tenant=self.tenant,
                uuid=None,
            )
            self.add(new_pf)

    def load_address(self, address: str, prefix: str, device: str, port: str, primary: bool = False, tags: list = []):
        """Load CitrixAdmAddress DiffSync model with specified data.

        Args:
            address (str): IP Address to be loaded.
            prefix (str): Prefix that IP Address resides in.
            device (str): Device that IP resides on.
            port (str): Interface that IP is configured on.
            primary (str): Whether the IP is primary IP for assigned device. Defaults to False.
            tags (list): List of tags assigned to IP. Defaults to [].
        """
        try:
            self.get(
                self.address,
                {
                    "address": address,
                    "prefix": prefix,
                    "device": device,
                    "port": port,
                },
            )
        except ObjectNotFound:
            new_addr = self.address(
                address=address,
                prefix=prefix,
                device=device,
                port=port,
                primary=primary,
                tenant=self.tenant,
                uuid=None,
                tags=tags,
            )
            self.add(new_addr)

    def load(self):
        """Load data from Citrix ADM into DiffSync models."""
        base_urls = [PLUGIN_CFG["base_url"], PLUGIN_CFG["additional_url"]]
        for url in base_urls:
            # init
            self.conn.url = url
            self.conn.login()
            self.adm_site_map = {}
            self.adm_device_map = {}

            self.create_site_map()
            self.load_devices()
            self.create_port_map()
            self.load_ports()
            self.load_addresses()

            self.conn.logout()
