"""Nautobot SSoT Citrix ADM Adapter for Citrix ADM SSoT plugin."""

from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from nautobot_ssot_citrix_adm.diffsync.models.citrix_adm import (
    CitrixAdmDatacenter,
    CitrixAdmDevice,


class CitrixAdmAdapter(DiffSync):
    """DiffSync adapter for Citrix ADM."""

    datacenter = CitrixAdmDatacenter
    device = CitrixAdmDevice

    def __init__(self, *args, job=None, sync=None, client=None, **kwargs):
        """Initialize Citrix ADM.

        Args:
            job (object, optional): Citrix ADM job. Defaults to None.
            sync (object, optional): Citrix ADM DiffSync. Defaults to None.
            client (object): Citrix ADM API client connection object.
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
    def load(self):
        """Load data from Citrix ADM into DiffSync models."""
        self.load_sites()
        self.load_devices()
