"""Nautobot DiffSync models for Citrix ADM SSoT."""
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Device as NewDevice
from nautobot.dcim.models import DeviceType, Location, LocationType, Manufacturer, Interface, Platform
from nautobot.extras.models import Role, Status
from nautobot.ipam.models import IPAddress, IPAddressToInterface
from nautobot.tenancy.models import Tenant
from nautobot_ssot_citrix_adm.diffsync.models.base import Datacenter, Device, Port, Address
from nautobot_ssot_citrix_adm.utils.nautobot import add_software_lcm, assign_version_to_device

try:
    import nautobot_device_lifecycle_mgmt  # noqa: F401

    LIFECYCLE_MGMT = True
except ImportError:
    LIFECYCLE_MGMT = False


class NautobotDatacenter(Datacenter):
    """Nautobot implementation of Citrix ADM Datacenter model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site in Nautobot from NautobotDatacenter object."""
        status_active = Status.objects.get(name="Active")
        global_region = Location.objects.get_or_create(
            name="Global", location_type=LocationType.objects.get(name="Region"), status=status_active
        )[0]
        site_loctype = LocationType.objects.get(name="Site")
        if Location.objects.filter(name=ids["name"]).exists():
            diffsync.job.logger.warning(f"Site {ids['name']} already exists so skipping creation.")
            return None
        new_site = Location(
            name=ids["name"],
            parent=global_region,
            status=status_active,
            latitude=attrs["latitude"],
            longitude=attrs["longitude"],
            location_type=site_loctype,
        )
        if ids.get("region"):
            new_site.parent = Location.objects.get_or_create(
                name=ids["region"], location_type=LocationType.objects.get(name="Region"), status=status_active
            )[0]
        new_site.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Site in Nautobot from NautobotDatacenter object."""
        if not settings.PLUGINS_CONFIG.get("nautobot_ssot_citrix_adm").get("update_sites"):
            self.diffsync.job.logger.warning(f"Update sites setting is disabled so skipping updating {self.name}.")
            return None
        site = Location.objects.get(id=self.uuid)
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
        lb_role, created = Role.objects.get_or_create(name=attrs["role"])
        if created:
            lb_role.content_types.add(ContentType.objects.get_for_model(NewDevice))
        lb_dt, _ = DeviceType.objects.get_or_create(
            model=attrs["model"], manufacturer=Manufacturer.objects.get(name="Citrix")
        )
        new_device = NewDevice(
            name=ids["name"],
            status=Status.objects.get(name=attrs["status"]),
            role=lb_role,
            location=Location.objects.get(name=attrs["site"]),
            device_type=lb_dt,
            serial=attrs["serial"],
            platform=Platform.objects.get(name="citrix.adc"),
        )
        if attrs.get("tenant"):
            new_device.tenant = Tenant.objects.update_or_create(name=attrs["tenant"])[0]
        if attrs.get("version"):
            new_device.custom_field_data.update({"os_version": attrs["version"]})
            if LIFECYCLE_MGMT:
                lcm_obj = add_software_lcm(diffsync=diffsync, platform="netscaler", version=attrs["version"])
                assign_version_to_device(diffsync=diffsync, device=new_device, software_lcm=lcm_obj)
        if attrs.get("hanode"):
            new_device.custom_field_data["ha_node"] = attrs["hanode"]
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
            device.role = Role.objects.get_or_create(name=attrs["role"])[0]
        if "serial" in attrs:
            device.serial = attrs["serial"]
        if "site" in attrs:
            device.location = Location.objects.get(name=attrs["site"])
        if "tenant" in attrs:
            if attrs.get("tenant"):
                device.tenant = Tenant.objects.update_or_create(name=attrs["tenant"])[0]
            else:
                device.tenant = None
        if "version" in attrs:
            device.custom_field_data.update({"os_version": attrs["version"]})
            if LIFECYCLE_MGMT:
                lcm_obj = add_software_lcm(diffsync=self.diffsync, platform="netscaler", version=attrs["version"])
                assign_version_to_device(diffsync=self.diffsync, device=device, software_lcm=lcm_obj)
        if "hanode" in attrs:
            device.custom_field_data["ha_node"] = attrs["hanode"]
        device.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Device in Nautobot from NautobotDevice object."""
        dev = NewDevice.objects.get(id=self.uuid)
        super().delete()
        self.diffsync.job.logger.info(f"Deleting Device {dev.name}.")
        self.diffsync.objects_to_delete["devices"].append(dev)
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
        self.diffsync.job.logger.info(f"Deleting Port {port.name} for {port.device.name}.")
        self.diffsync.objects_to_delete["ports"].append(port)
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
        )
        if attrs.get("tenant"):
            new_ip.tenant = Tenant.objects.update_or_create(name=attrs["tenant"])[0]
        if attrs.get("tags"):
            new_ip.tags.set(attrs["tags"])
        new_ip.validated_save()
        IPAddressToInterface.objects.create(ip_address=new_ip, interface=interface)
        if attrs.get("primary"):
            if new_ip.ip_version == 4:
                device.primary_ip4 = new_ip
            else:
                device.primary_ip6 = new_ip
            device.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update IP Address in Nautobot from NautobotAddress object."""
        addr = IPAddress.objects.get(id=self.uuid)
        if "primary" in attrs:
            device = NewDevice.objects.get(name=self.device)
            if addr.ip_version == 4:
                device.primary_ip4 = addr
            else:
                device.primary_ip6 = addr
            device.validated_save()
        if "tenant" in attrs:
            if attrs.get("tenant"):
                addr.tenant = Tenant.objects.update_or_create(name=attrs["tenant"])[0]
            else:
                addr.tenant = None
        if "tags" in attrs:
            addr.tags.set(attrs["tags"])
        else:
            addr.tags.clear()
        addr.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete IP Address in Nautobot from NautobotAddress object."""
        addr = IPAddress.objects.get(id=self.uuid)
        super().delete()
        self.diffsync.job.logger.info(f"Deleting IP Address {self}.")
        self.diffsync.objects_to_delete["addresses"].append(addr)
        return self
