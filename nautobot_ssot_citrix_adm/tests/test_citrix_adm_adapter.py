"""Test Citrix ADM adapter."""

import uuid
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from netutils.ip import netmask_to_cidr
from nautobot.extras.models import Job, JobResult
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_citrix_adm.diffsync.adapters.citrix_adm import CitrixAdmAdapter
from nautobot_ssot_citrix_adm.jobs import CitrixAdmDataSource
from nautobot_ssot_citrix_adm.tests.fixtures import SITE_FIXTURE_RECV, DEVICE_FIXTURE_RECV, PORT_FIXTURE_RECV


class TestCitrixAdmAdapterTestCase(TransactionTestCase):
    """Test NautobotSsotCitrixAdmAdapter class."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Initialize test case."""
        self.citrix_adm_client = MagicMock()
        self.citrix_adm_client.get_sites.return_value = SITE_FIXTURE_RECV
        self.citrix_adm_client.get_devices.return_value = DEVICE_FIXTURE_RECV
        self.citrix_adm_client.get_ports.return_value = PORT_FIXTURE_RECV

        self.job = CitrixAdmDataSource()
        self.job.kwargs["debug"] = True
        self.job.log_warning = MagicMock()
        self.job.log_info = MagicMock()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.citrix_adm = CitrixAdmAdapter(job=self.job, sync=None, client=self.citrix_adm_client)
        self.citrix_adm.load()

    def test_load_sites(self):
        """Test Nautobot SSoT Citrix ADM load_sites() function."""
        self.assertEqual(
            {f"{site['name']}__{site['region']}" for site in SITE_FIXTURE_RECV},
            {site.get_unique_id() for site in self.citrix_adm.get_all("datacenter")},
        )
        self.job.log_info.assert_called_with(
            message="Attempting to load DC: NTC Corporate HQ {'city': 'New York City', 'zipcode': '10018', 'type': '1', 'name': 'NTC Corporate HQ', 'region': 'North', 'country': 'USA', 'longitude': '-73.989429', 'id': '7d29e100-ae0c-4580-ba86-b72df0b6cfd8', 'latitude': '40.753146'}"
        )

    def test_load_sites_duplicate(self):
        """Test Nautobot SSoT Citrix ADM load_sites() function with duplicate sites."""
        self.citrix_adm.load_sites()
        self.job.log_warning.assert_called_with(
            message="Duplicate Site attempting to be loaded: {'city': 'New York City', 'zipcode': '10018', 'type': '1', 'name': 'NTC Corporate HQ', 'region': 'North', 'country': 'USA', 'longitude': '-73.989429', 'id': '7d29e100-ae0c-4580-ba86-b72df0b6cfd8', 'latitude': '40.753146'}."
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
            message="Duplicate Device attempting to be loaded: {'gateway': '1.81.7.1', 'mgmt_ip_address': '65.61.6.121', 'description': '', 'serialnumber': '98ATECSRNJ', 'display_name': '10.62.7.111-10.62.7.112', 'type': 'nsvpx', 'netmask': '255.255.255.0', 'datacenter_id': '28aa2970-0160-4860-aca8-a85f89268803', 'hostname': 'OGI-MSCI-IMS-Mctdgj-Pqsf-M', 'ip_address': '10.62.7.111', 'version': 'NetScaler NS12.1: Build 63.22.nc, Date: Oct 13 2021, 01:18:50   (64-bit)', 'instance_state': 'Up'}."
        )

    def test_load_devices_without_hostname(self):
        """Test the Nautobot SSoT Citrix ADM load_devices() function with a device missing hostname."""
        self.citrix_adm_client.get_devices.return_value = [{"hostname": ""}]
        self.citrix_adm.load_devices()
        self.job.log_warning.assert_called_once_with(
            message="Device without hostname will not be loaded. {'hostname': ''}"
        )

    def test_load_ports(self):
        """Test the Nautobot SSoT Citrix ADM load_ports() function."""
        mgmt_ports = list({f"Management__{port['hostname']}" for port in PORT_FIXTURE_RECV})
        non_mgmt_ports = [f"{port['devicename']}__{port['hostname']}" for port in PORT_FIXTURE_RECV]
        expected_ports = non_mgmt_ports + mgmt_ports
        actual_ports = [port.get_unique_id() for port in self.citrix_adm.get_all("port")]
        self.assertEqual(sorted(expected_ports), sorted(actual_ports))

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
            f"{port['ns_ip_address']}/{netmask_to_cidr(self.citrix_adm.adm_device_map[port['hostname']]['netmask'])}__{port['hostname']}__{port['devicename']}"
            for port in PORT_FIXTURE_RECV
        ]
        actual_addrs = [addr.get_unique_id() for addr in self.citrix_adm.get_all("address")]
        print(expected_addrs)
        print(actual_addrs)
        for addr in expected_addrs:
            self.assertTrue(addr in actual_addrs)
