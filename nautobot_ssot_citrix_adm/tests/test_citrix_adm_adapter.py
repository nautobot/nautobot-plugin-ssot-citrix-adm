"""Test Citrix ADM adapter."""

import json
import uuid
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from nautobot.extras.models import Job, JobResult
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_citrix_adm.diffsync.adapters.citrix_adm import CitrixAdmAdapter
from nautobot_ssot_citrix_adm.jobs import CitrixAdmDataSource


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


SITE_FIXTURE = []


class TestCitrixAdmAdapterTestCase(TransactionTestCase):
    """Test NautobotSsotCitrixAdmAdapter class."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Initialize test case."""
        self.citrix_adm_client = MagicMock()
        self.citrix_adm_client.get_sites.return_value = SITE_FIXTURE

        self.job = CitrixAdmDataSource()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.citrix_adm = CitrixAdmAdapter(job=self.job, sync=None, client=self.citrix_adm_client)

    def test_data_loading(self):
        """Test Nautobot SSoT Citrix ADM load() function."""
        # self.citrix_adm.load()
        # self.assertEqual(
        #     {site["name"] for site in SITE_FIXTURE},
        #     {site.get_unique_id() for site in self.citrix_adm.get_all("site")},
        # )
