"""Test Nautobot adapter."""
import uuid
from unittest.mock import MagicMock
from django.contrib.contenttypes.models import ContentType
from django.db.models import ProtectedError
from diffsync.exceptions import ObjectNotFound
from nautobot.dcim.models import (
    Device,
    DeviceType,
    DeviceRole,
    Interface,
    Manufacturer,
    Region,
    Site,
)
from nautobot.extras.models import Status, Job, JobResult
from nautobot.ipam.models import IPAddress
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
        core_router._custom_field_data["os_version"] = "1.2.3"  # pylint: disable=protected-access
        core_router._custom_field_data["system_of_record"] = "Citrix ADM"  # pylint: disable=protected-access
        core_router.validated_save()
        mgmt_intf = Interface.objects.create(name="Management", type="virtual", device=core_router)
        mgmt_intf.validated_save()

        mgmt_addr = IPAddress.objects.create(
            address="10.1.1.1/24",
            assigned_object_id=mgmt_intf.id,
            assigned_object_type=ContentType.objects.get_for_model(Interface),
            status=self.status_active,
        )
        mgmt_addr._custom_field_data["system_of_record"] = "Citrix ADM"  # pylint: disable=protected-access
        mgmt_addr.validated_save()
        mgmt_addr6 = IPAddress.objects.create(
            address="2001:db8:3333:4444:5555:6666:7777:8888/128",
            assigned_object_id=mgmt_intf.id,
            assigned_object_type=ContentType.objects.get_for_model(Interface),
            status=self.status_active,
        )
        mgmt_addr6._custom_field_data["system_of_record"] = "Citrix ADM"  # pylint: disable=protected-access
        mgmt_addr6.validated_save()

        core_router.primary_ip4 = mgmt_addr
        core_router.primary_ip6 = mgmt_addr6
        core_router.validated_save()

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

    def test_load_ports_success(self):
        """Test the load_ports() function success."""
        self.nb_adapter.load_devices()
        self.nb_adapter.load_ports()
        self.assertEqual(
            {"Management__edge-fw.test.com"},
            {port.get_unique_id() for port in self.nb_adapter.get_all("port")},
        )

    def test_load_ports_missing_device(self):
        """Test the load_ports() function with missing device."""
        self.nb_adapter.get = MagicMock()
        self.nb_adapter.get.side_effect = ObjectNotFound
        self.nb_adapter.load_ports()
        self.job.log_warning.assert_called_once_with(
            message="Unable to find edge-fw.test.com loaded so skipping loading port Management."
        )

    def test_load_addresses(self):
        """Test the load_addresses() function."""
        self.nb_adapter.load_addresses()
        self.assertEqual(
            {
                "10.1.1.1/24__edge-fw.test.com__Management",
                "2001:db8:3333:4444:5555:6666:7777:8888/128__edge-fw.test.com__Management",
            },
            {addr.get_unique_id() for addr in self.nb_adapter.get_all("address")},
        )

    def test_sync_complete(self):
        """Test the sync_complete() method in the NautobotAdapter."""
        self.nb_adapter.objects_to_delete = {
            "devices": [MagicMock()],
            "ports": [MagicMock()],
            "addresses": [MagicMock()],
        }
        self.nb_adapter.job = MagicMock()
        self.nb_adapter.job.log_info = MagicMock()

        deleted_objs = []
        for group in ["addresses", "ports", "devices"]:
            deleted_objs.extend(self.nb_adapter.objects_to_delete[group])

        self.nb_adapter.sync_complete(diff=MagicMock(), source=MagicMock())

        for obj in deleted_objs:
            self.assertTrue(obj.delete.called)
        self.assertEqual(len(self.nb_adapter.objects_to_delete["addresses"]), 0)
        self.assertEqual(len(self.nb_adapter.objects_to_delete["ports"]), 0)
        self.assertEqual(len(self.nb_adapter.objects_to_delete["devices"]), 0)
        self.assertTrue(self.nb_adapter.job.log_info.called)
        self.assertTrue(self.nb_adapter.job.log_info.call_count, 4)
        self.assertTrue(self.nb_adapter.job.log_info.call_args_list[0].startswith("Deleting"))
        self.assertTrue(self.nb_adapter.job.log_info.call_args_list[1].startswith("Deleting"))
        self.assertTrue(self.nb_adapter.job.log_info.call_args_list[2].startswith("Deleting"))
        self.assertTrue(self.nb_adapter.job.log_info.call_args_list[3].startswith("Deleting"))

    def test_sync_complete_protected_error(self):
        """
        Tests that ProtectedError exception is handled when deleting objects from Nautobot.
        """
        mock_dev = MagicMock()
        mock_dev.delete.side_effect = ProtectedError(msg="Cannot delete protected object.", protected_objects=mock_dev)
        self.nb_adapter.label_imported_objects = MagicMock(id="test")
        self.nb_adapter.objects_to_delete["devices"].append(mock_dev)
        self.nb_adapter.sync_complete(source=self.nb_adapter, diff=MagicMock())
        self.nb_adapter.label_imported_objects.assert_called_once()
        self.job.log_info.assert_called()
        self.job.log_info.calls[1].starts_with("Deletion failed protected object")

    def test_load(self):
        """Test the load() function."""
        self.nb_adapter.load_sites = MagicMock()
        self.nb_adapter.load_devices = MagicMock()
        self.nb_adapter.load_ports = MagicMock()
        self.nb_adapter.load_addresses = MagicMock()
        self.nb_adapter.load()
        self.nb_adapter.load_sites.assert_called_once()
        self.nb_adapter.load_devices.assert_called_once()
        self.nb_adapter.load_ports.assert_called_once()
        self.nb_adapter.load_addresses.assert_called_once()
