"""Jobs for Citrix ADM SSoT integration."""

from django.conf import settings
from diffsync.enum import DiffSyncFlags
from nautobot.extras.jobs import BooleanVar, Job
from nautobot_ssot.jobs.base import DataSource, DataTarget
from nautobot_ssot_citrix_adm.diffsync.adapters import citrix_adm, nautobot
from nautobot_ssot_citrix_adm.utils.citrix_adm import CitrixNitroClient


PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_ssot_citrix_adm"]

name = "Citrix ADM SSoT"  # pylint: disable=invalid-name


class CitrixAdmDataSource(DataSource, Job):
    """Citrix ADM SSoT Data Source."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)

    def __init__(self):
        """Initialize Citrix ADM Data Source."""
        super().__init__()
        self.diffsync_flags = self.diffsync_flags | DiffSyncFlags.CONTINUE_ON_FAILURE

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta data for Citrix ADM."""

        name = "Citrix ADM to Nautobot"
        data_source = "Citrix ADM"
        data_target = "Nautobot"
        description = "Sync information from Citrix ADM to Nautobot"

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataSource."""
        return {}

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return ()

    def load_source_adapter(self):
        """Load data from Citrix ADM into DiffSync models."""
        client = CitrixNitroClient(
            base_url=PLUGIN_CFG["base_url"],
            user=PLUGIN_CFG["username"],
            password=PLUGIN_CFG["password"],
            verify=PLUGIN_CFG["verify"],
        )
        self.source_adapter = citrix_adm.CitrixAdmAdapter(job=self, sync=self.sync, client=client)
        self.source_adapter.load()

    def load_target_adapter(self):
        """Load data from Nautobot into DiffSync models."""
        self.target_adapter = nautobot.NautobotAdapter(job=self, sync=self.sync)
        self.target_adapter.load()


class CitrixAdmDataTarget(DataTarget, Job):
    """Citrix ADM SSoT Data Target."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)

    def __init__(self):
        """Initialize Citrix ADM Data Target."""
        super().__init__()
        self.diffsync_flags = self.diffsync_flags | DiffSyncFlags.CONTINUE_ON_FAILURE

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta data for Citrix ADM."""

        name = "Nautobot to Citrix ADM"
        data_source = "Nautobot"
        data_target = "Citrix ADM"
        description = "Sync information from Nautobot to Citrix ADM"

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataTarget."""
        return {}

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return ()

    def load_source_adapter(self):
        """Load data from Nautobot into DiffSync models."""
        self.source_adapter = nautobot.NautobotAdapter(job=self, sync=self.sync)
        self.source_adapter.load()

    def load_target_adapter(self):
        """Load data from Citrix ADM into DiffSync models."""
        client = CitrixNitroClient(
            base_url=PLUGIN_CFG["base_url"],
            user=PLUGIN_CFG["username"],
            password=PLUGIN_CFG["password"],
            verify=PLUGIN_CFG["verify"],
        )
        self.target_adapter = citrix_adm.CitrixAdmAdapter(job=self, sync=self.sync, client=client)
        self.target_adapter.load()


jobs = [CitrixAdmDataSource]
