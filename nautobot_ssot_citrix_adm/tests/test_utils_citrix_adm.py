"""Utility functions for working with Citrix ADM."""

import logging
from unittest.mock import MagicMock, patch
from requests.exceptions import HTTPError
from nautobot.utilities.testing import TestCase
from nautobot_ssot_citrix_adm.tests.fixtures import (
    SITE_FIXTURE_SENT,
    SITE_FIXTURE_RECV,
    DEVICE_FIXTURE_SENT,
    DEVICE_FIXTURE_RECV,
    PORT_FIXTURE_SENT,
    PORT_FIXTURE_RECV,
)
from nautobot_ssot_citrix_adm.utils.citrix_adm import parse_hostname_for_role, parse_version, CitrixNitroClient

LOGGER = logging.getLogger(__name__)


class TestCitrixAdmClient(TestCase):
    """Test the Citrix ADM client and calls."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Configure common variables for tests."""
        self.base_url = "https://example.com"
        self.user = "user"
        self.password = "password"  # nosec: B105
        self.verify = True
        self.log = MagicMock()
        self.log.log_failure = MagicMock()
        self.log.log_info = MagicMock()
        self.client = CitrixNitroClient(self.base_url, self.user, self.password, self.log, self.verify)

    def test_init(self):
        """Validate the class initializer works as expected."""
        self.assertEqual(self.client.url, self.base_url)
        self.assertEqual(self.client.username, self.user)
        self.assertEqual(self.client.password, self.password)
        self.assertEqual(self.client.verify, self.verify)

    def test_url_updated(self):
        """Validate the URL is updated if a trailing slash is included in URL."""
        self.base_url = "https://example.com/"
        self.client = CitrixNitroClient(self.base_url, self.user, self.password, self.log, self.verify)
        self.assertEqual(self.client.url, self.base_url.rstrip("/"))

    @patch.object(CitrixNitroClient, "request")
    def test_login(self, mock_request):
        """Validate functionality of the login() method success."""
        mock_response = MagicMock()
        mock_response = {"login": [{"sessionid": "1234"}]}
        mock_request.return_value = mock_response
        self.client.login()
        self.assertEqual(self.client.headers["Cookie"], "SESSID=1234; path=/; SameSite=Lax; secure; HttpOnly")

    @patch.object(CitrixNitroClient, "request")
    def test_login_failure(self, mock_request):
        """Validate functionality of the login() method failure."""
        mock_response = MagicMock()
        mock_response = {}
        mock_request.return_value = mock_response
        self.client.login()
        self.log.log_failure.assert_called_once_with(
            message="Error while logging into Citrix ADM. Please validate your configuration is correct."
        )

    @patch.object(CitrixNitroClient, "request")
    def test_logout(self, mock_request):
        """Validate functionality of the logout() method success."""
        self.client.logout()
        mock_request.assert_called_with(
            method="POST",
            endpoint="config",
            objecttype="logout",
            data="object={'logout': {'username': 'user', 'password': 'password'}}",
        )

    @patch("nautobot_ssot_citrix_adm.utils.citrix_adm.requests.request")
    def test_request(self, mock_request):
        """Validate functionality of the request() method success."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = "Test successful!"
        mock_request.return_value = mock_response

        endpoint = "example"
        objecttype = "sample"
        objectname = "test"
        params = {"param1": "value1", "param2": "value2"}
        data = '{"key": "value"}'

        response = self.client.request("POST", endpoint, objecttype, objectname, params, data)

        mock_request.assert_called_with(
            method="POST",
            url="https://example.com/nitro/v1/example/sample/test?param1=value1param2=value2",
            data='{"key": "value"}',
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            verify=True,
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(response, "Test successful!")

    @patch("nautobot_ssot_citrix_adm.utils.citrix_adm.requests.request")
    def test_request_failure(self, mock_request):
        """Validate functionality of the request() method failure."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError
        mock_request.return_value = mock_response

        endpoint = "example"
        objecttype = "sample"
        objectname = "test"
        params = "test"
        data = '{"key": "value"}'

        self.client.request("POST", endpoint, objecttype, objectname, params, data)
        mock_response.raise_for_status.assert_called_once()
        self.log.log_failure.assert_called_once_with(message="Failure with request: ")

    @patch.object(CitrixNitroClient, "request")
    def test_get_sites_success(self, mock_request):
        """Validate functionality of the get_sites() method success."""
        mock_request.return_value = SITE_FIXTURE_SENT
        expected = self.client.get_sites()
        self.assertEqual(SITE_FIXTURE_RECV, expected)

    @patch.object(CitrixNitroClient, "request")
    def test_get_sites_failure(self, mock_request):
        """Validate functionality of the get_sites() method failure."""
        mock_request.return_value = {}
        expected = self.client.get_sites()
        self.log.log_failure.assert_called_once_with(message="Error getting sites from Citrix ADM.")
        self.assertEqual(expected, {})

    @patch.object(CitrixNitroClient, "request")
    def test_get_devices_success(self, mock_request):
        """Validate functionality of the get_devices() method success."""
        mock_request.return_value = DEVICE_FIXTURE_SENT
        expected = self.client.get_devices()
        self.assertEqual(DEVICE_FIXTURE_RECV, expected)

    @patch.object(CitrixNitroClient, "request")
    def test_get_devices_failure(self, mock_request):
        """Validate functionality of the get_devices() method failure."""
        mock_request.return_value = {}
        expected = self.client.get_devices()
        self.log.log_failure.assert_called_once_with(message="Error getting devices from Citrix ADM.")
        self.assertEqual(expected, {})

    @patch.object(CitrixNitroClient, "request")
    def test_get_ports_success(self, mock_request):
        """Validate functionality of the get_ports() method success."""
        mock_request.return_value = PORT_FIXTURE_SENT
        expected = self.client.get_ports()
        self.assertEqual(PORT_FIXTURE_RECV, expected)

    @patch.object(CitrixNitroClient, "request")
    def test_get_ports_failure(self, mock_request):
        """Validate functionality of the get_ports() method failure."""
        mock_request.return_value = {}
        expected = self.client.get_ports()
        self.log.log_failure.assert_called_once_with(message="Error getting ports from Citrix ADM.")
        self.assertEqual(expected, {})

    def test_parse_hostname_for_role_success(self):
        """Validate the functionality of the parse_hostname_for_role method success."""
        hostname_mapping = [(".*INT.*", "Internal"), (".*DMZ.*", "DMZ")]
        hostname = "INT-LB"
        result = parse_hostname_for_role(hostname_map=hostname_mapping, device_hostname=hostname)
        self.assertEqual(result, "Internal")

    def test_parse_hostname_for_role_failure(self):
        """Validate the functionality of the parse_hostname_for_role method failure."""
        hostname_mapping = []
        hostname = "Test LB"
        result = parse_hostname_for_role(hostname_map=hostname_mapping, device_hostname=hostname)
        self.assertEqual(result, "Load-Balancer")

    def test_parse_version(self):
        """Validate functionality of the parse_version function."""
        version = "NetScaler NS13.1: Build 37.38.nc, Date: Nov 23 2022, 04:42:36   (64-bit)"
        expected = "NS13.1: Build 37.38.nc"
        actual = parse_version(version=version)
        self.assertEqual(actual, expected)
