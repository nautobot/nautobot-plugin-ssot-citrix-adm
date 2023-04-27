"""Nautobot Adapter for Citrix ADM SSoT plugin."""

from diffsync import DiffSync
from nautobot.dcim.models import Site
from nautobot_ssot_citrix_adm.diffsync.models.nautobot import (
    NautobotDatacenter,


class NautobotAdapter(DiffSync):
    """DiffSync adapter for Nautobot."""

    datacenter = NautobotDatacenter

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize Nautobot.

        Args:
            job (object, optional): Nautobot job. Defaults to None.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync

    def load_sites(self):
        """Load Sites from Nautobot into DiffSync models."""
        for site in Site.objects.all():
            self.job.log_info(message=f"Loading Site {site.name} from Nautobot.")
            new_dc = self.datacenter(
                name=site.name,
                region=site.region.name,
                latitude=site.latitude,
                longitude=site.longitude,
                uuid=site.id,
            )
            self.add(new_dc)

    def load(self):
        """Load data from Nautobot into DiffSync models."""
        self.load_sites()
