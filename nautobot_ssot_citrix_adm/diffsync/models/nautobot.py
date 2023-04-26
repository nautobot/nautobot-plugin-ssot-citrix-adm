"""Nautobot DiffSync models for Citrix ADM SSoT."""
from nautobot.dcim.models import Device as NewDevice
from nautobot.dcim.models import Site, DeviceRole, DeviceType, Manufacturer
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress
from nautobot_ssot_citrix_adm.diffsync.models.base import Datacenter, Device, Port, Address


class NautobotDatacenter(Datacenter):
    """Nautobot implementation of Citrix ADM Datacenter model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site in Nautobot from NautobotDatacenter object."""
        new_site = Site(
            name=ids["name"],
            status=Status.objects.get_or_create(name=attrs["status"]),
        )
        new_site.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Site in Nautobot from NautobotDatacenter object."""
        site = Site.objects.get(id=self.uuid)
        if "status" in attrs:
            site.status = Status.objects.get_or_create(name=attrs["status"])
        site.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Site in Nautobot from NautobotDatacenter object."""
        site = Site.objects.get(id=self.uuid)
        super().delete()
        site.delete()
        return self


class NautobotDevice(Device):
    """Nautobot implementation of Citrix ADM Device model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Nautobot from NautobotDevice object."""
        new_device = NewDevice(
            name=ids["name"],
            status=Status.objects.get_or_create(name=attrs["status"]),
            role=DeviceRole.objects.get_or_create(name=attrs["role"]),
            site=Site.objects.get_or_create(name=attrs["site"]),
            device_type=DeviceType.objects.get_or_create(
                model=attrs["model"], manufacturer=Manufacturer.objects.get(name="Citrix")
            ),
        )
        new_device.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Nautobot from NautobotDevice object."""
        device = NewDevice.objects.get(id=self.uuid)
        if "status" in attrs:
            device.status = Status.objects.get_or_create(name=attrs["status"])
        if "role" in attrs:
            device.role = DeviceRole.objects.get_or_create(name=attrs["role"])
        if "site" in attrs:
            device.site = Site.objects.get_or_create(name=attrs["site"])
        device.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Device in Nautobot from NautobotDevice object."""
        dev = NewDevice.objects.get(id=self.uuid)
        super().delete()
        dev.delete()
        return self


class NautobotPort(Port):
    """Nautobot implementation of Citrix ADM Port model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Interface in Nautobot from NautobotPort object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Interface in Nautobot from NautobotPort object."""
        return super().update(attrs)

    def delete(self):
        """Delete Interface in Nautobot from NautobotPort object."""
        return self


class NautobotAddress(Address):
    """Nautobot implementation of Citrix ADM Address model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IP Address in Nautobot from NautobotAddress object."""
        new_ip = IPAddress(
            address=ids["address"],
            status=Status.objects.get_or_create(name=attrs["status"]),
        )
        new_ip.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update IP Address in Nautobot from NautobotAddress object."""
        site = Site.objects.get(id=self.uuid)
        if "status" in attrs:
            site.status = Status.objects.get_or_create(name=attrs["status"])
        site.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete IP Address in Nautobot from NautobotAddress object."""
        site = Site.objects.get(id=self.uuid)
        super().delete()
        site.delete()
        return self
