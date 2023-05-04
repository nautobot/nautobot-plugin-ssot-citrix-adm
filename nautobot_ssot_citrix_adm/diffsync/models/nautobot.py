"""Nautobot DiffSync models for Citrix ADM SSoT."""
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Device as NewDevice
from nautobot.dcim.models import Region, Site, DeviceRole, DeviceType, Manufacturer, Interface, Platform
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
            status=Status.objects.get(name="Active"),
            latitude=attrs["latitude"],
            longitude=attrs["longitude"],
        )
        if ids.get("region"):
            new_site.region, _ = Region.objects.get_or_create(name=ids["region"])
        new_site.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Site in Nautobot from NautobotDatacenter object."""
        site = Site.objects.get(id=self.uuid)
        if "latitude" in attrs:
            site.latitude = attrs["latitude"]
        if "longitude" in attrs:
            site.longitude = attrs["longitude"]
        site.validated_save()
        return super().update(attrs)


class NautobotDevice(Device):
    """Nautobot implementation of Citrix ADM Device model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Nautobot from NautobotDevice object."""
        lb_role, _ = DeviceRole.objects.get_or_create(name="Load-Balancer")
        lb_dt, _ = DeviceType.objects.get_or_create(
            model=attrs["model"], manufacturer=Manufacturer.objects.get(name="Citrix")
        )
        new_device = NewDevice(
            name=ids["name"],
            status=Status.objects.get(name=attrs["status"]),
            device_role=lb_role,
            site=Site.objects.get(name=attrs["site"]),
            device_type=lb_dt,
            serial=attrs["serial"],
            platform=Platform.objects.get(slug="netscaler"),
        )
        if attrs.get("version"):
            new_device.custom_field_data.update({"os_version": attrs["version"]})
        new_device.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Nautobot from NautobotDevice object."""
        device = NewDevice.objects.get(id=self.uuid)
        if "model" in attrs:
            device.device_type, _ = DeviceType.objects.get_or_create(
                model=attrs["model"], manufacturer=Manufacturer.objects.get(name="Citrix")
            )
        if "status" in attrs:
            device.status = Status.objects.get(name=attrs["status"])
        if "role" in attrs:
            device.device_role, _ = DeviceRole.objects.get_or_create(name="Load-Balancer")
        if "serial" in attrs:
            device.serial = attrs["serial"]
        if "site" in attrs:
            device.site = Site.objects.get(name=attrs["site"])
        if attrs.get("version"):
            device.custom_field_data.update({"os_version": attrs["version"]})
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
        new_port = Interface(
            name=ids["name"],
            device=NewDevice.objects.get(name=ids["device"]),
            status=Status.objects.get(name=attrs["status"]),
            description=attrs["description"],
            type="virtual",
            mgmt_only=bool(ids["name"] == "Management"),
        )
        new_port.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Interface in Nautobot from NautobotPort object."""
        port = Interface.objects.get(self.uuid)
        if "status" in attrs:
            port.status = Status.objects.get(name=attrs["status"])
        if "description" in attrs:
            port.description = attrs["description"]
        port.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Interface in Nautobot from NautobotPort object."""
        port = Interface.objects.get(id=self.uuid)
        super().delete()
        port.delete()
        return self


class NautobotAddress(Address):
    """Nautobot implementation of Citrix ADM Address model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IP Address in Nautobot from NautobotAddress object."""
        device = NewDevice.objects.get(name=ids["device"])
        interface = Interface.objects.get(name=ids["port"], device=device)
        new_ip = IPAddress(
            address=ids["address"],
            status=Status.objects.get(name="Active"),
            assigned_object_type=ContentType.objects.get_for_model(Interface),
            assigned_object_id=interface.id,
        )
        new_ip.validated_save()
        if attrs.get("primary"):
            if new_ip.family == 4:
                device.primary_ip4 = new_ip
            else:
                device.primary_ip6 = new_ip
            device.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update IP Address in Nautobot from NautobotAddress object."""
        addr = IPAddress.objects.get(id=self.uuid)
        if "primary" in attrs:
            device = addr.assigned_object.device
            if addr.family == 4:
                device.primary_ip4 = addr
            else:
                device.primary_ip6 = addr
            device.validated_save()
        addr.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete IP Address in Nautobot from NautobotAddress object."""
        addr = IPAddress.objects.get(id=self.uuid)
        super().delete()
        addr.delete()
        return self
