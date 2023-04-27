"""Utility functions for working with Citrix ADM."""

import logging
from nautobot.utilities.testing import TestCase
from nautobot_ssot_citrix_adm.utils.citrix_adm import parse_version

LOGGER = logging.getLogger(__name__)


class TestCitrixAdmClient(TestCase):
    """Test the Citrix ADM client and calls."""

    databases = ("default", "job_logs")

    def test_parse_version(self):
        """Validate functionality of the parse_version function."""
        version = "NetScaler NS13.1: Build 37.38.nc, Date: Nov 23 2022, 04:42:36   (64-bit)"
        expected = "NS13.1: Build 37.38.nc"
        actual = parse_version(version=version)
        self.assertEqual(actual, expected)
