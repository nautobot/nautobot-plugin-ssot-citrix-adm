"""Test Citrix ADM adapter."""
import uuid
from unittest.mock import MagicMock
from diffsync.exceptions import ObjectNotFound
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Device, DeviceRole, DeviceType, Interface, Manufacturer, Site
from nautobot.extras.models import CustomField, Job, JobResult, Status
from nautobot.ipam.models import IPAddress
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_citrix_adm.diffsync.adapters.citrix_adm import CitrixAdmAdapter
from nautobot_ssot_citrix_adm.jobs import CitrixAdmDataSource
from nautobot_ssot_citrix_adm.tests.fixtures import (
    SITE_FIXTURE_RECV,
    DEVICE_FIXTURE_RECV,
    VLAN_FIXTURE_RECV,
    NSIP6_FIXTURE_RECV,
    ADM_DEVICE_MAP_FIXTURE,
)


class TestCitrixAdmAdapterTestCase(TransactionTestCase):  # pylint: disable=too-many-instance-attributes
    """Test NautobotSsotCitrixAdmAdapter class."""

    databases = ("default", "job_logs")

    def __init__(self, *args, **kwargs):
        """Initialize test case."""
        self.sor_cf = None
        self.status_active = None
        self.hq_site = None
        self.test_dev = None
        self.intf = None
        self.addr = None
        super().__init__(*args, **kwargs)

    def setUp(self):
        """Configure shared objects for test cases."""
        super().setUp()
        self.citrix_adm_client = MagicMock()
        self.citrix_adm_client.get_sites.return_value = SITE_FIXTURE_RECV
        self.citrix_adm_client.get_devices.return_value = DEVICE_FIXTURE_RECV
        self.citrix_adm_client.get_vlan_bindings.side_effect = VLAN_FIXTURE_RECV
        self.citrix_adm_client.get_nsip6.side_effect = NSIP6_FIXTURE_RECV
        self.job = CitrixAdmDataSource()
        self.job.kwargs["debug"] = True
        self.job.log_warning = MagicMock()
        self.job.log_info = MagicMock()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.citrix_adm = CitrixAdmAdapter(job=self.job, sync=None, client=self.citrix_adm_client)

    def test_load_site(self):
        """Test Nautobot SSoT Citrix ADM load_site() function."""
        self.citrix_adm.load_site(site_info=SITE_FIXTURE_RECV[2])
        self.assertEqual(
            {"ARIA__West"},
            {site.get_unique_id() for site in self.citrix_adm.get_all("datacenter")},
        )
        self.job.log_info.assert_called_with(message="Attempting to load DC: ARIA")

    def test_load_site_duplicate(self):
        """Test Nautobot SSoT Citrix ADM load_site() function with duplicate site."""
        site_info = SITE_FIXTURE_RECV[4]
        self.citrix_adm.load_site(site_info=site_info)
        self.citrix_adm.load_site(site_info=site_info)
        self.job.log_warning.assert_called_with(
            message="Duplicate Site attempting to be loaded: {'city': 'New York City', 'zipcode': '10018', 'type': '1', 'name': 'NTC Corporate HQ', 'region': 'North', 'country': 'USA', 'longitude': '-73.989429', 'id': '7d29e100-ae0c-4580-ba86-b72df0b6cfd8', 'latitude': '40.753146'}."
        )

    def test_load_devices(self):
        """Test the Nautobot SSoT Citrix ADM load_devices() function."""
        self.citrix_adm.adm_site_map[DEVICE_FIXTURE_RECV[0]["datacenter_id"]] = SITE_FIXTURE_RECV[1]
        self.citrix_adm_client.get_devices.return_value = [DEVICE_FIXTURE_RECV[0]]
        self.citrix_adm.load_devices()
        self.assertEqual(
            {"UYLLBFRCXM55-EA"},
            {dev.get_unique_id() for dev in self.citrix_adm.get_all("device")},
        )

    def test_load_devices_duplicate(self):
        """Test the Nautobot SSoT Citrix ADM load_devices() function with duplicate devices."""
        self.citrix_adm.adm_site_map[DEVICE_FIXTURE_RECV[3]["datacenter_id"]] = SITE_FIXTURE_RECV[2]
        self.citrix_adm_client.get_devices.return_value = [DEVICE_FIXTURE_RECV[3]]
        self.citrix_adm.load_devices()
        self.citrix_adm.load_devices()
        self.job.log_warning.assert_called_with(
            message="Duplicate Device attempting to be loaded: OGI-MSCI-IMS-Mctdgj-Pqsf-M"
        )

    def test_load_devices_without_hostname(self):
        """Test the Nautobot SSoT Citrix ADM load_devices() function with a device missing hostname."""
        self.citrix_adm_client.get_devices.return_value = [{"hostname": ""}]
        self.citrix_adm.load_devices()
        self.job.log_warning.assert_called_with(message="Device without hostname will not be loaded. {'hostname': ''}")

    def test_load_ports(self):
        """Test the Nautobot SSoT Citrix ADM load_ports() function."""
        self.citrix_adm.adm_device_map = ADM_DEVICE_MAP_FIXTURE
        self.citrix_adm.get = MagicMock()
        self.citrix_adm.get.side_effect = [ObjectNotFound, MagicMock(), ObjectNotFound, MagicMock()]
        self.citrix_adm.load_ports()
        expected_ports = {
            f"{port['port']}__{adc['hostname']}"
            for _, adc in self.citrix_adm.adm_device_map.items()
            for port in adc["ports"]
        }
        expected_ports = list(expected_ports)
        actual_ports = [port.get_unique_id() for port in self.citrix_adm.get_all("port")]
        self.assertEqual(sorted(expected_ports), sorted(actual_ports))

    def test_port_addresses_loaded(self):
        """Test the Nautobot SSoT Citrix ADM loads port addresses."""
        self.citrix_adm.adm_device_map = ADM_DEVICE_MAP_FIXTURE
        self.citrix_adm.get = MagicMock()
        self.citrix_adm.get.side_effect = [ObjectNotFound, ObjectNotFound]
        self.citrix_adm.adm_device_map = ADM_DEVICE_MAP_FIXTURE
        self.citrix_adm.get = MagicMock()
        self.citrix_adm.get.side_effect = [ObjectNotFound, ObjectNotFound]
        self.citrix_adm.load_addresses()
        expected_addrs = [
            f"{port['ipaddress']}/{port['netmask']}__{adc['hostname']}__{port['port']}"
            for _, adc in self.citrix_adm.adm_device_map.items()
            for port in adc["ports"]
            if port.get("ipaddress")
        ]
        actual_addrs = [addr.get_unique_id() for addr in self.citrix_adm.get_all("address")]
        self.assertEqual(sorted(expected_addrs), sorted(actual_addrs))

    def test_label_imported_objects_not_found(self):
        """Validate the label_imported_objects() handling ObjectNotFound."""
        mock_response = MagicMock()
        mock_response.get_unique_id = MagicMock()
        mock_response.get_unique_id.return_value = "Test"

        target = MagicMock()
        target.get = MagicMock(side_effect=ObjectNotFound)
        self.citrix_adm.label_object = MagicMock()
        self.citrix_adm.label_imported_objects(target)
        self.citrix_adm.label_object.assert_not_called()

    def build_nautobot_objects(self):
        """Build common Nautobot objects for tests."""
        self.sor_cf = CustomField.objects.get(name="system_of_record")
        self.status_active = Status.objects.get(name="Active")
        self.hq_site = Site.objects.create(name="HQ", slug="hq", status=self.status_active)
        self.hq_site.validated_save()

        citrix_manu, _ = Manufacturer.objects.get_or_create(name="Citrix")
        srx_devicetype, _ = DeviceType.objects.get_or_create(model="SDX", manufacturer=citrix_manu)
        core_role, _ = DeviceRole.objects.get_or_create(name="CORE")

        self.test_dev = Device.objects.create(
            name="Test",
            device_type=srx_devicetype,
            device_role=core_role,
            serial="AB234567",
            site=self.hq_site,
            status=self.status_active,
        )
        self.test_dev.custom_field_data["os_version"] = "1.2.3"
        self.test_dev.validated_save()
        self.intf = Interface.objects.create(name="Management", type="virtual", device=self.test_dev)
        self.intf.validated_save()

        self.addr = IPAddress.objects.create(
            address="10.10.10.1/24",
            assigned_object_id=self.intf.id,
            assigned_object_type=ContentType.objects.get_for_model(Interface),
            status=self.status_active,
        )
        self.addr.validated_save()

    def test_label_object_instance_found(self):
        """Validate the label_object() handling when DiffSync instance is found."""
        self.build_nautobot_objects()
        mock_dev = MagicMock()
        mock_dev.name = "Test"
        mock_intf = MagicMock()
        mock_intf.name = "Management"
        mock_intf.device = "Test"
        mock_addr = MagicMock()
        mock_addr.address = "10.10.10.1/24"
        mock_addr.device = "Test"
        mock_addr.port = "Management"

        self.citrix_adm.get = MagicMock()
        self.citrix_adm.get.side_effect = [mock_dev, mock_intf, mock_addr]

        self.citrix_adm.label_object("device", self.test_dev.name)
        self.citrix_adm.label_object("port", f"{self.intf.name}__{self.test_dev.name}")
        self.citrix_adm.label_object("address", f"{self.addr.address}__{self.test_dev.name}__{self.intf.name}")

        self.intf.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.intf.custom_field_data)
        self.addr.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.addr.custom_field_data)

    def test_label_object_when_object_not_found(self):
        """Validate the label_object() handling ObjectNotFound."""
        self.build_nautobot_objects()
        self.citrix_adm.label_object("device", self.test_dev.name)
        self.citrix_adm.label_object("port", f"{self.intf.name}__{self.test_dev.name}")
        self.citrix_adm.label_object("address", f"{self.addr.address}__{self.test_dev.name}__{self.intf.name}")

        self.test_dev.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.test_dev.custom_field_data)
        self.intf.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.intf.custom_field_data)
        self.addr.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.addr.custom_field_data)
