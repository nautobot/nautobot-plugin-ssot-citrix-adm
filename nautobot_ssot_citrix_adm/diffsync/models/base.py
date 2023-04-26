"""DiffSyncModel subclasses for Nautobot-to-Citrix ADM data sync."""
from typing import Optional
from uuid import UUID
from diffsync import DiffSyncModel


class Datacenter(DiffSyncModel):
    """Diffsync model for Citrix ADM datacenters."""

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
        "serial",
        "site",
        "status",
        "version",
    )
    _children = {}

    name: str
    model: Optional[str]
    serial: Optional[str]
    site: Optional[str]
    status: Optional[str]
    version: Optional[str]

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


class Address(DiffSyncModel):
    """DiffSync model for Citrix ADM management addresses."""

    _modelname = "address"
    _identifiers = ("address",)
    _attributes = ("device",)
    _children = {}

    address: str
    device: str

    uuid: Optional[UUID]
