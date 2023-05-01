"""Test Nautobot adapter."""
import uuid
from unittest.mock import MagicMock
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import (
    Device,
    DeviceType,
    DeviceRole,
    Interface,
    Manufacturer,
    Region,
    Site,
)
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField, Status, Job, JobResult
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
        self.build_nautobot_objects()

    def build_nautobot_objects(self):
        """Build out Nautobot objects to test loading."""
        self.ny_region = Region.objects.create(name="NY", slug="ny")
        self.ny_region.validated_save()

        self.hq_site = Site.objects.create(region=self.ny_region, name="HQ", slug="hq", status=self.status_active)
        self.hq_site.validated_save()

        citrix_manu, _ = Manufacturer.objects.get_or_create(name="Citrix")
        srx_devicetype, _ = DeviceType.objects.get_or_create(model="SDX", manufacturer=citrix_manu)
        core_role, _ = DeviceRole.objects.get_or_create(name="CORE")

        core_router = Device.objects.create(
            name="edge-fw.test.com",
            device_type=srx_devicetype,
            device_role=core_role,
            serial="FQ123456",
            site=self.hq_site,
            status=self.status_active,
        )
        cf_dict = {
            "name": "os_version",
            "slug": "os_version",
            "type": CustomFieldTypeChoices.TYPE_TEXT,
            "label": "OS Version",
        }
        cfield, _ = CustomField.objects.get_or_create(name=cf_dict["name"], defaults=cf_dict)
        cfield.content_types.add(ContentType.objects.get_for_model(Device))
        core_router.custom_field_data["os_version"] = "1.2.3"
        core_router.validated_save()
        mgmt_intf = Interface.objects.create(name="Management", type="virtual", device=core_router)
        mgmt_intf.validated_save()

    def test_load_sites(self):
        """Test the load_sites() function."""
        self.nb_adapter.load_sites()
        self.assertEqual(
            {
                "HQ__NY",
            },
            {site.get_unique_id() for site in self.nb_adapter.get_all("datacenter")},
        )
        self.job.log_info.assert_called_once_with(message="Loading Site HQ from Nautobot.")

    def test_load_devices(self):
        """Test the load_devices() function."""
        self.nb_adapter.load_devices()
        self.assertEqual(
            {"edge-fw.test.com"},
            {dev.get_unique_id() for dev in self.nb_adapter.get_all("device")},
        )
        self.job.log_info.assert_called_once_with(message="Loading Device edge-fw.test.com from Nautobot.")
