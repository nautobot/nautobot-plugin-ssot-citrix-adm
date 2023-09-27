"""Test Citrix ADM adapter."""
import uuid
from unittest.mock import MagicMock
from diffsync.exceptions import ObjectNotFound
from django.contrib.contenttypes.models import ContentType
from netutils.ip import netmask_to_cidr
from nautobot.dcim.models import Device, DeviceRole, DeviceType, Interface, Manufacturer, Site
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField, Job, JobResult, Status
from nautobot.ipam.models import IPAddress
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_citrix_adm.diffsync.adapters.citrix_adm import CitrixAdmAdapter
from nautobot_ssot_citrix_adm.jobs import CitrixAdmDataSource
from nautobot_ssot_citrix_adm.tests.fixtures import (
    SITE_FIXTURE_RECV,
    DEVICE_FIXTURE_RECV,
    PORT_FIXTURE_RECV,
    VLAN_FIXTURE_RECV,
    NSIP6_FIXTURE_RECV,
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
        self.citrix_adm_client.get_ports.return_value = PORT_FIXTURE_RECV
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
        self.citrix_adm.load()

    def test_load_site(self):
        """Test Nautobot SSoT Citrix ADM load_site() function."""
        self.assertEqual(
            {"ARIA__West", "Delta HQ__East"},
            {site.get_unique_id() for site in self.citrix_adm.get_all("datacenter")},
        )
        self.job.log_info.assert_called_with(message="Attempting to load DC: ARIA")

    def test_load_site_duplicate(self):
        """Test Nautobot SSoT Citrix ADM load_site() function with duplicate site."""
        site_info = {
            "name": "NTC Corporate HQ",
            "region": "North",
            "longitude": "-73.989429",
            "id": "7d29e100-ae0c-4580-ba86-b72df0b6cfd8",
            "latitude": "40.753146",
        }
        self.citrix_adm.load_site(site_info=site_info)
        self.job.log_warning.assert_called_with(
            message="Duplicate Site attempting to be loaded: {'city': 'Atlanta', 'zipcode': '30009', 'type': '1', 'name': 'Delta HQ', 'region': 'East', 'country': 'USA', 'longitude': '-84.320000', 'id': '28aa2970-0160-4860-aca8-a85f89268803', 'latitude': '34.030000'}."
        )

    def test_load_devices(self):
        """Test the Nautobot SSoT Citrix ADM load_devices() function."""
        self.assertEqual(
            {dev["hostname"] for dev in DEVICE_FIXTURE_RECV},
            {dev.get_unique_id() for dev in self.citrix_adm.get_all("device")},
        )

    def test_load_devices_duplicate(self):
        """Test the Nautobot SSoT Citrix ADM load_devices() function with duplicate devices."""
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
        expected_ports = {
            f"{port['port']}__{adc['hostname']}"
            for _, adc in self.citrix_adm.adm_device_map.items()
            for port in adc["ports"]
        }
        expected_ports.update({f"Management__{adc['hostname']}" for _, adc in self.citrix_adm.adm_device_map.items()})
        expected_ports = list(expected_ports)
        actual_ports = [port.get_unique_id() for port in self.citrix_adm.get_all("port")]
        self.assertEqual(sorted(expected_ports), sorted(actual_ports))

    '''def test_load_ports_duplicate(self):
        """Test the Nautobot SSoT Citrix ADM load_ports() function with duplicate ports."""
        self.citrix_adm.load_ports()
        self.job.log_warning.assert_called_with(
            message="Duplicate port 10/1 attempting to be loaded for OGI-MSCI-IMS-Mctdgj-Pqsf-M."
        )'''

    '''def test_load_ports_missing_device(self):
        """Test the Nautobot SSoT Citrix ADM load_ports() function with a missing device."""
        self.citrix_adm_client.get_ports.return_value = [{"devicename": "10/1", "hostname": "Test"}]
        self.citrix_adm.get = MagicMock()
        self.citrix_adm.get.side_effect = [ObjectNotFound, ObjectNotFound]
        self.citrix_adm.load_ports()
        self.job.log_warning.assert_called_with(message="Unable to find device Test so skipping loading of port 10/1.")'''

    def test_management_addresses_loaded(self):
        """Test the Nautobot SSoT Citrix ADM loads management addresses."""
        expected_addrs = [
            f"{addr['mgmt_ip_address']}/{netmask_to_cidr(addr['netmask'])}__{addr['hostname']}__Management"
            for addr in DEVICE_FIXTURE_RECV
        ]
        actual_addrs = [addr.get_unique_id() for addr in self.citrix_adm.get_all("address")]
        for addr in expected_addrs:
            self.assertTrue(addr in actual_addrs)

    def test_port_addresses_loaded(self):
        """Test the Nautobot SSoT Citrix ADM loads port addresses."""
        expected_addrs = [
            f"{port['ipaddress']}/{port['netmask']}__{adc['hostname']}__{port['port']}"
            for _, adc in self.citrix_adm.adm_device_map.items()
            for port in adc["ports"]
            if port.get("ipaddress")
        ]
        expected_addrs.extend(
            f"{adc['mgmt_ip_address']}/{netmask_to_cidr(adc['netmask'])}__{adc['hostname']}__Management"
            for _, adc in self.citrix_adm.adm_device_map.items()
        )
        actual_addrs = [addr.get_unique_id() for addr in self.citrix_adm.get_all("address")]
        for addr in expected_addrs:
            self.assertTrue(addr in actual_addrs)

    '''def test_management_port_updated(self):
        """Test the Nautobot SSoT Citrix ADM updates management port if IP found on another."""
        update_port = {
            "devicename": "LO/1",
            "ns_ip_address": "85.52.0.128",
            "state": "ENABLED",
            "hostname": "OLQE-WHOO-KAL-WKH-SndJhcc3-X",
            "description": "",
        }
        self.citrix_adm_client.get_ports.return_value = PORT_FIXTURE_RECV + [update_port]
        self.citrix_adm.load_ports()
        self.job.log_info.assert_called_with(
            message="Management address 85.52.0.128 found on LO/1 so updating DiffSync models to use this port."
        )'''

    def test_label_imported_objects_custom_field(self):
        """Validate the label_imported_objects() successfully creates CustomField."""
        target = MagicMock()
        self.citrix_adm.label_object = MagicMock()
        self.citrix_adm.label_imported_objects(target)
        dev_customfield = CustomField.objects.get(name="ssot_last_synchronized")
        self.assertEqual(dev_customfield.type, CustomFieldTypeChoices.TYPE_DATE)
        self.assertEqual(dev_customfield.label, "Last sync from System of Record")
        device_ct = ContentType.objects.get_for_model(Device)
        self.assertIn(dev_customfield, device_ct.custom_fields.all())
        self.citrix_adm.label_object.assert_called()

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

        self.citrix_adm.label_object("device", self.test_dev.name, self.sor_cf)
        self.citrix_adm.label_object("port", f"{self.intf.name}__{self.test_dev.name}", self.sor_cf)
        self.citrix_adm.label_object(
            "address", f"{self.addr.address}__{self.test_dev.name}__{self.intf.name}", self.sor_cf
        )

        self.intf.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.intf.custom_field_data)
        self.addr.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.addr.custom_field_data)

    def test_label_object_when_object_not_found(self):
        """Validate the label_object() handling ObjectNotFound."""
        self.build_nautobot_objects()
        self.citrix_adm.label_object("device", self.test_dev.name, self.sor_cf)
        self.citrix_adm.label_object("port", f"{self.intf.name}__{self.test_dev.name}", self.sor_cf)
        self.citrix_adm.label_object(
            "address", f"{self.addr.address}__{self.test_dev.name}__{self.intf.name}", self.sor_cf
        )

        self.test_dev.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.test_dev.custom_field_data)
        self.intf.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.intf.custom_field_data)
        self.addr.refresh_from_db()
        self.assertIn(self.sor_cf.name, self.addr.custom_field_data)
