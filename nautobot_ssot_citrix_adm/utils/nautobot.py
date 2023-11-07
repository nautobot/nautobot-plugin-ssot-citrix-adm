"""Utility functions for working with Nautobot."""
from typing import List, OrderedDict
from uuid import UUID
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import Relationship, RelationshipAssociation
from taggit.managers import TaggableManager
from netutils.ip import netmask_to_cidr, is_ip_within

try:
    from nautobot_device_lifecycle_mgmt.models import SoftwareLCM

    LIFECYCLE_MGMT = True
except ImportError:
    LIFECYCLE_MGMT = False


def add_software_lcm(diffsync, platform: str, version: str):
    """Add OS Version as SoftwareLCM if Device Lifecycle Plugin found.

    Args:
        diffsync (DiffSyncAdapter): DiffSync adapter with Job and maps.
        platform (str): Name of platform to associate version to.
        version (str): The software version to be created for specified platform.

    Returns:
        UUID: UUID of the OS Version that is being found or created.
    """
    platform = Platform.objects.get(slug=platform)
    try:
        os_ver = SoftwareLCM.objects.get(device_platform=platform, version=version).id
    except SoftwareLCM.DoesNotExist:
        diffsync.job.log_info(message=f"Creating Version {version} for {platform}.")
        os_ver = SoftwareLCM(
            device_platform=platform,
            version=version,
        )
        os_ver.validated_save()
        os_ver = os_ver.id
    return os_ver


def assign_version_to_device(diffsync, device: Device, software_lcm: UUID):
    """Add Relationship between Device and SoftwareLCM."""
    try:
        software_relation = Relationship.objects.get(slug="device_soft")
        relationship = RelationshipAssociation.objects.get(relationship=software_relation, destination_id=device.id)
        diffsync.job.log_warning(
            message=f"Deleting Software Version Relationships for {device.name} to assign a new version."
        )
        relationship.delete()
    except RelationshipAssociation.DoesNotExist:
        pass
    new_assoc = RelationshipAssociation(
        relationship=Relationship.objects.get(slug="device_soft"),
        source_type=ContentType.objects.get_for_model(SoftwareLCM),
        source_id=software_lcm,
        destination_type=ContentType.objects.get_for_model(Device),
        destination_id=device.id,
    )
    new_assoc.validated_save()


def get_tag_strings(list_tags: TaggableManager) -> List[str]:
    """Gets string values of all Tags in a list.

    This is the opposite of the `get_tags` function.

    Args:
        list_tags (TaggableManager): List of Tag objects to convert to strings.

    Returns:
        List[str]: List of string values matching the Tags passed in.
    """
    _strings = list(list_tags.names())
    if len(_strings) > 1:
        _strings.sort()
    return _strings

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