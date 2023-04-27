"""Nautobot SSoT Citrix ADM Adapter for Citrix ADM SSoT plugin."""

from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from nautobot_ssot_citrix_adm.diffsync.models.citrix_adm import (
    CitrixAdmDatacenter,
    CitrixAdmDevice,
    CitrixAdmPort,
)
from nautobot_ssot_citrix_adm.utils.citrix_adm import parse_version, CitrixNitroClient


class CitrixAdmAdapter(DiffSync):
    """DiffSync adapter for Citrix ADM."""

    datacenter = CitrixAdmDatacenter
    device = CitrixAdmDevice
    port = CitrixAdmPort

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

    def load_sites(self):
        """Load sites from Citrix ADM into DiffSync models."""
        sites = self.conn.get_sites()
        for site in sites:
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
            try:
                found_dev = self.get(self.device, dev["hostname"])
                if found_dev:
                    self.job.log_warning(message=f"Duplicate Device attempting to be loaded: {dev}.")
            except ObjectNotFound:
                new_dev = self.device(
                    name=dev["hostname"],
                    model=dev["type"],
                    serial=dev["serialnumber"],
                    site=self.adm_site_map[dev["datacenter_id"]],
                    status="Active" if dev["instance_state"] == "Up" else "Offline",
                    version=parse_version(dev["version"]),
                    uuid=None,
                )
                self.add(new_dev)

    def load_ports(self):
        """Load ports from Citrix ADM into DiffSync models."""
        ports = self.conn.get_ports()
        for port in ports:
            try:
                dev = self.get(self.device, port["hostname"])
                new_port = self.port(
                    name=port["devicename"],
                    device=port["hostname"],
                    status="Active" if port.get("state") == "ENABLED" else "Offline",
                    description=port["description"],
                    uuid=None,
                )
                self.add(new_port)
                dev.add_child(new_port)
            except ObjectNotFound:
                self.job.log_warning(
                    message=f"Unable to find device {port['hostname']} so skipping loading of port {port['devicename']}."
                )

    def load(self):
        """Load data from Citrix ADM into DiffSync models."""
        self.load_sites()
        self.load_devices()
        self.load_ports()
