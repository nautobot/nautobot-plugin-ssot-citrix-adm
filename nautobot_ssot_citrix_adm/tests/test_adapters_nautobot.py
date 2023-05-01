"""Test Nautobot adapter."""
import uuid
from unittest.mock import MagicMock
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import (
    Region,
    Site,
)
from nautobot.extras.models import Status, Job, JobResult
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_citrix_adm.diffsync.adapters.nautobot import NautobotAdapter
from nautobot_ssot_citrix_adm.jobs import CitrixAdmDataSource


class NautobotDiffSyncTestCase(TransactionTestCase):
    """Test the NautobotAdapter class."""

    databases = ("default", "job_logs")

    def __init__(self, *args, **kwargs):
        """Initialize shared variables."""
        super().__init__(*args, **kwargs)
        self.ny_region = None
        self.hq_site = None

    def setUp(self):  # pylint: disable=too-many-locals
        """Per-test-case data setup."""
        super().setUp()
        self.status_active = Status.objects.get(name="Active")

        self.job = CitrixAdmDataSource()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.nb_adapter = NautobotAdapter(job=self.job, sync=None)
        self.job.log_info = MagicMock()
        self.job.log_warning = MagicMock()

    def build_nautobot_objects(self):
        """Build out Nautobot objects to test loading."""
        self.ny_region = Region.objects.create(name="NY", slug="ny")
        self.ny_region.validated_save()

        self.hq_site = Site.objects.create(region=self.ny_region, name="HQ", slug="hq", status=self.status_active)
        self.hq_site.validated_save()

    def test_data_loading(self):
        """Test the load() function."""
        self.build_nautobot_objects()
        self.nb_adapter.load()

        self.assertEqual(
            {
                "HQ__NY",
            },
            {site.get_unique_id() for site in self.nb_adapter.get_all("datacenter")},
        )
        self.job.log_info.assert_called_once_with(message="Loading Site HQ from Nautobot.")
