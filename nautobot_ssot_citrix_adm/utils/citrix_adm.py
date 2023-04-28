"""Utility functions for working with Citrix ADM."""
import re
from typing import Union, Optional
import requests


# based on client found at https://github.com/slauger/python-nitro
class CitrixNitroClient:
    """Client for interacting with Citrix ADM NITRO API."""

    def __init__(  # pylint: disable=too-many-arguments
        self, base_url: str, user: str, password: str, logger, verify: bool = True
    ):
        """Initialize NITRO client.

        Args:
            base_url (str): Base URL for MAS/ADM API. Must include schema, http(s).
            user (str): Username to authenticate with Citrix ADM.
            password (str): Password to authenticate with Citrix ADM.
            verify (bool, optional): Whether to validate SSL certificate on Citrix ADM or not. Defaults to True.
            logger (Job): Job logger to notify users of progress.
        """
        self.url = base_url
        self.username = user
        self.password = password
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.verify = verify
        self.log = logger

    def login(self):
        """Login to ADM/MAS and set authorization token to enable further communication."""
        url = "config"
        objecttype = "login"
        login = {"login": {"username": self.username, "password": self.password}}
        payload = f"object={login}"
        response = self.request(method="POST", endpoint=url, objecttype=objecttype, data=payload)
        if response:
            session_id = response["login"][0]["sessionid"]
            self.headers["Cookie"] = f"SESSID={session_id}; path=/; SameSite=Lax; secure; HttpOnly"
        else:
            self.log.log_failure(
                message="Error while logging into Citrix ADM. Please validate your configuration is correct."
            )

    def logout(self):
        """Best practice to logout when session is complete."""
        url = "config"
        objecttype = "logout"
        self.request(method="POST", endpoint=url, objecttype=objecttype)

    def request(  # pylint: disable=too-many-arguments
        self,
        method: str,
        endpoint: str,
        objecttype: str = "",
        objectname: str = "",
        params: Optional[Union[str, dict]] = None,
        data: Optional[str] = None,
    ):
        """Perform request of specified method to endpoint.

        Args:
            method (str): HTTP method to use with request, ie GET, PUT, POST, etc.
            endpoint (str): API endpoint to query.
            objecttype (str, optional): Specific object type to query the API about. Defaults to "".
            objectname (str, optional): Specifc object to query the API about. Defaults to "".
            params (Optional[Union[str, dict]], optional): Additional parameters for the request. Defaults to None.
            data (Optional[str], optional): Addiontal data payload for the request. Defaults to None.

        Returns:
            dict: Dictionary of data about objectname of objecttype with specified parameters if specified.
        """
        url = self.url + "/nitro/v1/" + endpoint + "/" + objecttype

        if objectname:
            url += "/" + objectname

        if params:
            url += "?"

            if isinstance(params, dict):
                for key, value in params.items():
                    url += key + "=" + value
            else:
                url += params

        _result = requests.request(
            method=method,
            url=url,
            data=data,
            headers=self.headers,
            verify=self.verify,
        )
        try:
            _result.raise_for_status()
            return _result.json()
        except requests.exceptions.HTTPError as err:
            self.log.log_failure(message=f"Failure with request: {err}")
            return {}

    def get_sites(self):
        """Gather all sites configured on MAS/ADM instance."""
        self.log.log_info(message="Getting sites from Citrix ADM.")
        endpoint = "config"
        objecttype = "mps_datacenter"
        params = {"attrs": "city,zipcode,type,name,region,country,latitude,longitude,id"}
        result = self.request("GET", endpoint, objecttype, params=params)
        if result:
            return result[objecttype]
        self.log.log_failure(message="Error getting sites from Citrix ADM.")
        return {}

    def get_devices(self):
        """Gather all devices registered to MAS/ADM instance."""
        self.log.log_info(message="Getting devices from Citrix ADM.")
        endpoint = "config"
        objecttype = "managed_device"
        params = {
            "attrs": "ip_address,hostname,gateway,mgmt_ip_address,description,serialnumber,type,display_name,netmask,datacenter_id,version,instance_state"
        }
        result = self.request("GET", endpoint, objecttype, params=params)
        if result:
            return result[objecttype]
        self.log.log_failure(message="Error getting devices from Citrix ADM.")
        return {}

    def get_ports(self):
        """Gather all ports registered to devices in MAS/ADM instance."""
        self.log.log_info(message="Getting ports from Citrix ADM.")
        endpoint = "config"
        objecttype = "ns_network_interface"
        params = {"attrs": "devicename,ns_ip_address,state,hostname,description"}
        result = self.request("GET", endpoint, objecttype, params=params)
        if result:
            return result[objecttype]
        self.log.log_failure(message="Error getting ports from Citrix ADM.")
        return {}


def parse_version(version: str):
    """Parse Device version from string.

    Args:
        version (str): Version string from device API query.
    """
    result = ""
    match_pattern = r"NetScaler\s(?P<version>NS\d+\.\d+: Build\s\d+\.\d+\.\w+)"
    match = re.match(pattern=match_pattern, string=version)
    if match:
        result = match.group("version")
    return result
