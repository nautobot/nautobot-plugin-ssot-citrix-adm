"""Utility functions for working with Citrix ADM."""
import re
from typing import List, Union, Optional, Tuple
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
        if base_url.endswith("/"):
            base_url = base_url.rstrip("/")
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
        logout = {"logout": {"username": self.username, "password": self.password}}
        payload = f"object={logout}"
        self.headers.pop("_MPS_API_PROXY_MANAGED_INSTANCE_IP", None)
        self.headers.pop("_MPS_API_PROXY_MANAGED_INSTANCE_USERNAME", None)
        self.headers.pop("_MPS_API_PROXY_MANAGED_INSTANCE_PASSWORD", None)
        self.request(method="POST", endpoint=url, objecttype=objecttype, data=payload)

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
            self.log.log_warning(message=f"Failure with request: {err}")
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
    
    def get_nsip(self, adc):
        """Gather all nsip addresses from ADC instance using ADM as proxy."""
        endpoint = "config"
        objecttype = "nsip"
        params = {}
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_USERNAME"] = self.username
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_PASSWORD"] = self.password
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_IP"] = adc["ip_address"]
        result = self.request("GET", endpoint, objecttype, params=params)
        if result:
            return result[objecttype]
        self.log.log_warning(message=f"Error getting nsip from {adc['hostname']}")
        return {}

    def get_nsip6(self, adc):
        """Gather all nsip6 addresses from ADC instance using ADM as proxy."""
        endpoint = "config"
        objecttype = "nsip6"
        params = {}
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_USERNAME"] = self.username
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_PASSWORD"] = self.password
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_IP"] = adc["ip_address"]
        result = self.request("GET", endpoint, objecttype, params=params)
        if result:
            return result[objecttype]
        self.log.log_warning(message=f"Error getting nsip6 from {adc['hostname']}")

        return {}

    def get_vlan_bindings(self, adc):
        """Gather all interface vlan and nsip bindings from ADC instance using ADM as proxy."""
        endpoint = "config"
        objecttype = "vlan_binding"
        params = {"bulkbindings": "yes"}
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_USERNAME"] = self.username
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_PASSWORD"] = self.password
        self.headers["_MPS_API_PROXY_MANAGED_INSTANCE_IP"] = adc["ip_address"]
        result = self.request("GET", endpoint, objecttype, params=params)
        if result:
            return result[objecttype]
        self.log.log_warning(message=f"Error getting vlan bindings from {adc['hostname']}")

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


def parse_hostname_for_role(hostname_map: List[Tuple[str, str]], device_hostname: str):
    """Parse device hostname from hostname_map to get Device Role.

    Args:
        hostname_map (List[Tuple[str, str]]): List of tuples containing regex to compare with hostname and associated DeviceRole name.
        device_hostname (str): Hostname of Device to determine role of.

    Returns:
        str: Name of DeviceRole. Defaults to Load-Balancer.
    """
    device_role = "Load-Balancer"
    if hostname_map:
        for entry in hostname_map:
            match = re.match(pattern=entry[0], string=device_hostname)
            if match:
                device_role = entry[1]
    return device_role

def parse_vlan_bindings(vlan_bindings: List[dict]) -> List[dict]:
    """Parses output from get_vlan_bindings() into a list of ports and bound addresses.
    
    Args:
        vlan_bindings: Output from get_vlan_bindings().

    Returns:
        List[dict]: List of ports and bound addresses.
    """
    ports = []
    for binding in vlan_bindings:
        if binding.get("vlan_nsip_binding"):
            for nsip in binding["vlan_nsip_binding"]:
                vlan = nsip["id"]
                ipaddress = nsip["ipaddress"]
                netmask = netmask_to_cidr(nsip["netmask"])
                port = binding["vlan_port_binding"][0]["ifnum"]
                record = {"vlan": vlan, "ipaddress": ipaddress, "netmask": netmask, "port": port}
                ports.append(record)
        if binding.get("vlan_nsip6_binding"):
            for nsip6 in binding["vlan_nsip6_binding"]:
                vlan = nsip6["id"]
                ipaddress, netmask = nsip6["ipaddress"].split("/")
                port = binding["vlan_port_binding"][0]["ifnum"]
                record = {"vlan": vlan, "ipaddress": ipaddress, "netmask": netmask, "port": port}
                ports.append(record)
                
    return ports

def parse_nsips(nsips : List[dict], ports : List[dict]) -> List[dict]:
    """Parse Netscaler IPv4 Addresses
    Args:
        nsips (List[dict]): Output from get_nsips().
        ports (List[dict]): Output from get_vlan_bindings().
    
    Returns:
        List[dict]: List of ports and bound addresses.
    """
    for nsip in nsips:
        if nsip["type"] == "NSIP":
            for port in ports:
                # add a tag to existing record
                if port["ipaddress"] == nsip["ipaddress"]:
                    port["tags"] = ["NSIP"]
                    break
        if nsip["type"] == "SNIP":
            for port in ports:
                # skip if already found
                if port["ipaddress"] == nsip["ipaddress"]:
                    break
                # compare SNIP to bound addresses to determine port
                if is_ip_within(nsip["ipaddress"], f"{port['ipaddress']}/{port['netmask']}"):
                    port = port["port"]
                    vlan = port["vlan"]
                    ipaddress = nsip["ipaddress"]
                    netmask = netmask_to_cidr(nsip["netmask"])
                    record = {"vlan": vlan, "ipaddress": ipaddress, "netmask": netmask, "port": port}
                    ports.append(record)
    return ports

def parse_nsip6s(nsip6s : List[dict], ports : List[dict]) -> List[dict]:
    """Parse Netscaler IPv6 Addresses

    Args:
        nsip6s (List[dict]): Output from get_nsip6s().
        ports (List[dict]): Output from get_vlan_bindings().

    Returns:
        List[dict]: List of ports and bound addresses.
    """
    for nsip6 in nsip6s:
        if nsip6["scope"] == "link-local":
            vlan = nsip6["vlan"]
            ipaddress, netmask = nsip6["ipv6address"].split("/")
            port = "L0/1"
            record = {"vlan": vlan, "ipaddress": ipaddress, "netmask": netmask, "port": port}
            ports.append(record)

    return ports