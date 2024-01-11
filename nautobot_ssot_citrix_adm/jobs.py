"""Jobs for Citrix ADM SSoT integration."""

from django.conf import settings
from nautobot.core.celery import register_jobs
from nautobot.extras.jobs import BooleanVar, Job, MultiObjectVar, ObjectVar
from nautobot.extras.models import ExternalIntegration
from nautobot.tenancy.models import Tenant
from nautobot_ssot.jobs.base import DataSource, DataTarget
from nautobot_ssot_citrix_adm.diffsync.adapters import citrix_adm, nautobot


PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_ssot_citrix_adm"]

name = "Citrix ADM SSoT"  # pylint: disable=invalid-name


class CitrixAdmDataSource(DataSource, Job):  # pylint: disable=too-many-instance-attributes
    """Citrix ADM SSoT Data Source."""

    instances = MultiObjectVar(
        model=ExternalIntegration,
        queryset=ExternalIntegration.objects.all(),
        display_field="display",
        label="Citrix ADM Instances",
        required=True,
    )
    tenant = ObjectVar(model=Tenant, queryset=Tenant.objects.all(), display_field="display_name", required=False)
    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)

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
        self.source_adapter = citrix_adm.CitrixAdmAdapter(
            job=self, sync=self.sync, instances=self.instances, tenant=self.tenant
        )
        self.source_adapter.load()

    def load_target_adapter(self):
        """Load data from Nautobot into DiffSync models."""
        self.target_adapter = nautobot.NautobotAdapter(job=self, sync=self.sync)
        self.target_adapter.load()

    def run(  # pylint: disable=arguments-differ, too-many-arguments
        self, dryrun, memory_profiling, instances, tenant, debug, *args, **kwargs
    ):
        """Perform data synchronization."""
        self.instances = instances
        self.tenant = tenant
        self.debug = debug
        self.dryrun = dryrun
        self.memory_profiling = memory_profiling
        super().run(dryrun=self.dryrun, memory_profiling=self.memory_profiling, *args, **kwargs)


class CitrixAdmDataTarget(DataTarget, Job):
    """Citrix ADM SSoT Data Target."""

    instances = ObjectVar(
        model=ExternalIntegration,
        queryset=ExternalIntegration.objects.all(),
        display_field="display",
        label="Citrix ADM Instance",
        required=True,
    )
    tenant = ObjectVar(model=Tenant, queryset=Tenant.objects.all(), display_field="display_name", required=False)
    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)

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
        self.target_adapter = citrix_adm.CitrixAdmAdapter(
            job=self, sync=self.sync, instances=self.instance, tenant=self.tenant
        )
        self.target_adapter.load()

    def run(  # pylint: disable=arguments-differ, too-many-arguments
        self, dryrun, memory_profiling, instance, tenant, debug, *args, **kwargs
    ):
        """Perform data synchronization."""
        self.instance = instance
        self.tenant = tenant
        self.debug = debug
        self.dryrun = dryrun
        self.memory_profiling = memory_profiling
        super().run(dryrun=self.dryrun, memory_profiling=self.memory_profiling, *args, **kwargs)


jobs = [CitrixAdmDataSource]
register_jobs(*jobs)
