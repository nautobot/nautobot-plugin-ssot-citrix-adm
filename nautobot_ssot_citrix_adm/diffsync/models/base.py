"""DiffSyncModel subclasses for Nautobot-to-Citrix ADM data sync."""
from typing import List, Optional
from uuid import UUID
from diffsync import DiffSyncModel
from diffsync.enum import DiffSyncModelFlags


class Datacenter(DiffSyncModel):
    """Diffsync model for Citrix ADM datacenters."""

    model_flags = DiffSyncModelFlags.SKIP_UNMATCHED_DST

    _modelname = "datacenter"
    _identifiers = (
        "name",
        "region",
    )
    _attributes = ("latitude", "longitude")

    name: str
    region: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    uuid: Optional[UUID]


class Device(DiffSyncModel):
    """DiffSync model for Citrix ADM devices."""

    _modelname = "device"
    _identifiers = ("name",)
    _attributes = (
        "model",
        "role",
        "serial",
        "site",
        "status",
        "tenant",
        "version",
        "hanode",
    )
    _children = {"port": "ports"}

    name: str
    model: Optional[str]
    role: str
    serial: Optional[str]
    site: Optional[str]
    status: Optional[str]
    tenant: Optional[str]
    version: Optional[str]
    ports: Optional[List["Port"]] = []
    hanode: Optional[str]

    uuid: Optional[UUID]


class Port(DiffSyncModel):
    """DiffSync model for Citrix ADM device interfaces."""

    _modelname = "port"
    _identifiers = ("name", "device")
    _attributes = ("status", "description")
    _children = {}

    name: str
    device: str
    status: str
    description: Optional[str]

    uuid: Optional[UUID]


class Subnet(DiffSyncModel):
    """DiffSync model for Citrix ADM management prefixes."""

    _modelname = "prefix"
    _identifiers = ("prefix", "namespace")
    _attributes = ("tenant",)
    _children = {}

    prefix: str
    namespace: str
    tenant: Optional[str]

    uuid: Optional[UUID]


class Address(DiffSyncModel):
    """DiffSync model for Citrix ADM IP Addresses."""

    _modelname = "address"
    _identifiers = ("address", "prefix")
    _attributes = ("tenant", "tags")
    _children = {}

    address: str
    prefix: str
    tenant: Optional[str]
    tags: Optional[list]

    uuid: Optional[UUID]


class IPAddressOnInterface(DiffSyncModel):
    """DiffSync model for Citrix ADM tracking IPAddress on particular Device interfaces."""

    _modelname = "ip_on_intf"
    _identifiers = ("address", "device", "port")
    _attributes = ("primary",)
    _children = {}

    address: str
    device: str
    port: str
    primary: bool

    uuid: Optional[UUID]
