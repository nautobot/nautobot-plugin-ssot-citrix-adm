"""Tests to validate utility functions for Nautobot."""

from unittest.mock import MagicMock
from nautobot.dcim.models import Platform
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_citrix_adm.utils.nautobot import add_software_lcm

try:  # pylint: disable=duplicate-code
    from nautobot_device_lifecycle_mgmt.models import SoftwareLCM

    LIFECYCLE_MGMT = True
except ImportError:
    LIFECYCLE_MGMT = False


class TestUtilsNautobot(TransactionTestCase):
    """Test Nautobot utility functions."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Setup shared objects for testing."""
        self.platform, _ = Platform.objects.get_or_create(name="Test")
        self.diffsync = MagicMock()
        self.diffsync.job.log_info = MagicMock()

    def test_add_software_lcm_existing_version(self):
        """Test the add_software_lcm() function with an existing version."""
        version = "1.0"
        soft_lcm = SoftwareLCM.objects.create(device_platform=self.platform, version=version)
        result = add_software_lcm(self.diffsync, self.platform.slug, version)
        self.assertEqual(result, soft_lcm.id)
        self.diffsync.job.log_info.assert_not_called()

    def test_add_software_lcm_new_version(self):
        """Test the add_software_lcm() function with a new version."""
        version = "2.0"
        result = add_software_lcm(self.diffsync, self.platform.slug, version)
        soft_lcm = SoftwareLCM.objects.get(device_platform=self.platform, version=version)
        self.assertEqual(result, soft_lcm.id)
        self.diffsync.job.log_info.assert_called_once_with(message="Creating Version 2.0 for Test.")
