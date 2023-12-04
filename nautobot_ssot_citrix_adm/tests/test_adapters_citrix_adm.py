"""Test Citrix ADM adapter."""
from unittest.mock import MagicMock
from diffsync.exceptions import ObjectNotFound
from nautobot.extras.models import JobResult
from nautobot.core.testing import TransactionTestCase
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
        self.job.debug = True
        self.job.logger.warning = MagicMock()
        self.job.logger.info = MagicMock()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, task_name="fake task", worker="default"
        )
        self.citrix_adm = CitrixAdmAdapter(job=self.job, sync=None, client=self.citrix_adm_client)

    def test_load_site(self):
        """Test Nautobot SSoT Citrix ADM load_site() function."""
        self.citrix_adm.load_site(site_info=SITE_FIXTURE_RECV[2])
        self.assertEqual(
            {"ARIA__West"},
            {site.get_unique_id() for site in self.citrix_adm.get_all("datacenter")},
        )
        self.job.logger.info.assert_called_with("Attempting to load DC: ARIA")

    def test_load_site_duplicate(self):
        """Test Nautobot SSoT Citrix ADM load_site() function with duplicate site."""
        site_info = SITE_FIXTURE_RECV[4]
        self.job.debug = True
        self.citrix_adm.load_site(site_info=site_info)
        self.citrix_adm.load_site(site_info=site_info)
        self.job.logger.warning.assert_called_with(
            "Duplicate Site attempting to be loaded: {'city': 'New York City', 'zipcode': '10018', 'type': '1', 'name': 'NTC Corporate HQ', 'region': 'North', 'country': 'USA', 'longitude': '-73.989429', 'id': '7d29e100-ae0c-4580-ba86-b72df0b6cfd8', 'latitude': '40.753146'}."
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
        self.job.logger.warning.assert_called_with(
            "Duplicate Device attempting to be loaded: OGI-MSCI-IMS-Mctdgj-Pqsf-M"
        )

    def test_load_devices_without_hostname(self):
        """Test the Nautobot SSoT Citrix ADM load_devices() function with a device missing hostname."""
        self.citrix_adm_client.get_devices.return_value = [{"hostname": ""}]
        self.citrix_adm.load_devices()
        self.job.logger.warning.assert_called_with("Device without hostname will not be loaded. {'hostname': ''}")

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

    def test_load_addresses(self):
        """Test the Nautobot SSoT Citrix ADM load_addresses() function."""
        self.citrix_adm.adm_device_map = ADM_DEVICE_MAP_FIXTURE
        self.citrix_adm.load_prefix = MagicMock()
        self.citrix_adm.load_address = MagicMock()
        self.citrix_adm.load_address_to_interface = MagicMock()
        self.citrix_adm.load_addresses()
        self.citrix_adm.load_prefix.assert_called_with(prefix="192.168.1.0/24")
        self.citrix_adm.load_address.assert_called_with(
            address="192.168.1.5/24",
            prefix="192.168.1.0/24",
            tags=["MGMT"],
        )
        self.citrix_adm.load_address_to_interface.assert_called_with(
            address="192.168.1.5/24", device="TEST", port="0/1", primary=True
        )

    def test_load_prefix(self):
        """Test the Nautobot SSoT Citrix ADM load_prefix() function."""
        self.citrix_adm.load_prefix(prefix="10.0.0.0/16")
        self.assertEqual({"10.0.0.0/16__Global"}, {pf.get_unique_id() for pf in self.citrix_adm.get_all("prefix")})

    def test_load_address(self):
        """Test the Nautobot SSoT Citrix ADM load_address() function."""
        self.citrix_adm.load_address(address="10.0.0.1/24", prefix="10.0.0.0/24", tags=["TEST"])
        self.assertEqual(
            {"10.0.0.1/24__10.0.0.0/24"},
            {addr.get_unique_id() for addr in self.citrix_adm.get_all("address")},
        )

    def test_load_address_to_interface(self):
        """Test the Nautobot SSoT Citrix ADM load_address_to_interface() function."""
        self.citrix_adm.load_address_to_interface(address="10.0.0.1/24", device="TEST", port="mgmt", primary=True)
        self.assertEqual(
            {"10.0.0.1/24__TEST__mgmt"}, {map.get_unique_id() for map in self.citrix_adm.get_all("ip_on_intf")}
        )
