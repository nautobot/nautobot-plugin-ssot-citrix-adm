"""Test Citrix ADM adapter."""

import uuid
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from nautobot.extras.models import Job, JobResult
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_citrix_adm.diffsync.adapters.citrix_adm import CitrixAdmAdapter
from nautobot_ssot_citrix_adm.jobs import CitrixAdmDataSource
from nautobot_ssot_citrix_adm.tests.fixtures import SITE_FIXTURE, DEVICE_FIXTURE, PORT_FIXTURE


class TestCitrixAdmAdapterTestCase(TransactionTestCase):
    """Test NautobotSsotCitrixAdmAdapter class."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Initialize test case."""
        self.citrix_adm_client = MagicMock()
        self.citrix_adm_client.get_sites.return_value = SITE_FIXTURE["mps_datacenter"]
        self.citrix_adm_client.get_devices.return_value = DEVICE_FIXTURE["managed_device"]
        self.citrix_adm_client.get_ports.return_value = PORT_FIXTURE["ns_network_interface"]

        self.job = CitrixAdmDataSource()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.citrix_adm = CitrixAdmAdapter(job=self.job, sync=None, client=self.citrix_adm_client)

    def test_data_loading(self):
        """Test Nautobot SSoT Citrix ADM load() function."""
        self.citrix_adm.load()
        self.assertEqual(
            {f"{site['name']}__{site['region']}" for site in SITE_FIXTURE["mps_datacenter"]},
            {site.get_unique_id() for site in self.citrix_adm.get_all("datacenter")},
        )
        self.assertEqual(
            {dev["hostname"] for dev in DEVICE_FIXTURE["managed_device"]},
            {dev.get_unique_id() for dev in self.citrix_adm.get_all("device")},
        )
        self.assertEqual(
            {f"{port['devicename']}__{port['hostname']}" for port in PORT_FIXTURE["ns_network_interface"]},
            {port.get_unique_id() for port in self.citrix_adm.get_all("port")},
        )
