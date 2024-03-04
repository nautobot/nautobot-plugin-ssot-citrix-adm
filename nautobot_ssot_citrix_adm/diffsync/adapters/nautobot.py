"""Nautobot Adapter for Citrix ADM SSoT plugin."""

from collections import defaultdict
from diffsync import DiffSync
from diffsync.enum import DiffSyncModelFlags
from diffsync.exceptions import ObjectNotFound
from django.db.models import ProtectedError
from typing import Optional
from nautobot.dcim.models import Device as OrmDevice
from nautobot.dcim.models import Interface, Location, LocationType
from nautobot.extras.models import Job, Relationship, RelationshipAssociation
from nautobot.ipam.models import IPAddress, IPAddressToInterface, Prefix
from nautobot.tenancy.models import Tenant
from nautobot_ssot_citrix_adm.diffsync.models.nautobot import (
    NautobotAddress,
    NautobotDatacenter,
    NautobotDevice,
    NautobotPort,
    NautobotSubnet,
    NautobotIPAddressOnInterface,
)
from nautobot_ssot_citrix_adm.utils import nautobot

try:
    import nautobot_device_lifecycle_mgmt  # noqa: F401

    LIFECYCLE_MGMT = True
except ImportError:
    LIFECYCLE_MGMT = False


class NautobotAdapter(DiffSync):
    """DiffSync adapter for Nautobot."""

    datacenter = NautobotDatacenter
    device = NautobotDevice
    port = NautobotPort
    prefix = NautobotSubnet
    address = NautobotAddress
    ip_on_intf = NautobotIPAddressOnInterface

    top_level = ["datacenter", "device", "prefix", "address", "ip_on_intf"]

    def __init__(self, *args, job: Job, sync=None, tenant: Optional[Tenant] = None, **kwargs):
        """Initialize Nautobot.

        Args:
            job (Job): Nautobot job.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
            tenant (Tenant, optional): Tenant to associate imported objects with. Used to filter loaded objects.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.tenant = tenant
        self.objects_to_delete = defaultdict(list)

    def load_sites(self):
        """Load Sites from Nautobot into DiffSync models."""
        site_loctype = LocationType.objects.get(name="Site")
        for site in Location.objects.filter(location_type=site_loctype):
            if self.job.debug:
                self.job.logger.info(f"Loading Site {site.name} from Nautobot.")
            new_dc = self.datacenter(
                name=site.name,
                region=site.parent.name if site.parent else "",
                latitude=float(round(site.latitude, 6)) if site.latitude else None,
                longitude=float(round(site.longitude, 6)) if site.longitude else None,
                uuid=site.id,
            )
            self.add(new_dc)

    def load_devices(self):
        """Load Devices from Nautobot into DiffSync models."""
        if self.tenant:
            devices = OrmDevice.objects.select_related("device_type", "location", "status").filter(tenant=self.tenant)
        else:
            devices = OrmDevice.objects.select_related("device_type", "location", "status").filter(
                _custom_field_data__system_of_record="Citrix ADM"
            )
        for dev in devices:
            if self.job.debug:
                self.job.logger.info(f"Loading Device {dev.name} from Nautobot.")
            version = dev._custom_field_data["os_version"]
            hanode = dev._custom_field_data.get("ha_node")
            if LIFECYCLE_MGMT:
                try:
                    software_relation = Relationship.objects.get(label="Software on Device")
                    relationship = RelationshipAssociation.objects.get(
                        relationship=software_relation, destination_id=dev.id
                    )
                    version = relationship.source.version
                except RelationshipAssociation.DoesNotExist:
                    self.job.logger.info(f"Unable to find DLC Software version for {dev.name}.")
                    version = ""
            new_dev = self.device(
                name=dev.name,
                model=dev.device_type.model,
                role=dev.role.name,
                serial=dev.serial,
                site=dev.location.name,
                status=dev.status.name,
                tenant=dev.tenant.name if dev.tenant else "",
                version=version,
                uuid=dev.id,
                hanode=hanode,
            )
            if self.tenant:
                new_dev.model_flags = DiffSyncModelFlags.SKIP_UNMATCHED_DST
            self.add(new_dev)

    def load_ports(self):
        """Load Interfaces from Nautobot into DiffSync models."""
        if self.tenant:
            interfaces = Interface.objects.select_related("device", "status").filter(device__tenant=self.tenant)
        else:
            interfaces = Interface.objects.select_related("device", "status").filter(
                device___custom_field_data__system_of_record="Citrix ADM"
            )
        for intf in interfaces:
            try:
                dev = self.get(self.device, intf.device.name)
                new_intf = self.port(
                    name=intf.name,
                    device=intf.device.name,
                    status=intf.status.name,
                    description=intf.description,
                    uuid=intf.id,
                )
                if self.tenant:
                    new_intf.model_flags = DiffSyncModelFlags.SKIP_UNMATCHED_DST
                self.add(new_intf)
                dev.add_child(new_intf)
            except ObjectNotFound:
                self.job.logger.warning(
                    f"Unable to find {intf.device.name} loaded so skipping loading port {intf.name}."
                )

    def load_prefixes(self):
        """Load Prefixes from Nautobot into DiffSync models."""
        if self.tenant:
            prefixes = Prefix.objects.filter(tenant=self.tenant)
        else:
            prefixes = Prefix.objects.filter(_custom_field_data__system_of_record="Citrix ADM")
        for pf in prefixes:
            new_pf = self.prefix(
                prefix=str(pf.prefix),
                namespace=pf.namespace.name,
                tenant=pf.tenant.name if pf.tenant else None,
                uuid=pf.id,
            )
            if self.tenant:
                new_pf.model_flags = DiffSyncModelFlags.SKIP_UNMATCHED_DST
            self.add(new_pf)

    def load_addresses(self):
        """Load IP Addresses from Nautobot into DiffSync models."""
        if self.tenant:
            addresses = IPAddress.objects.filter(tenant=self.tenant)
        else:
            addresses = IPAddress.objects.filter(_custom_field_data__system_of_record="Citrix ADM")
        for addr in addresses:
            new_ip = self.address(
                address=str(addr.address),
                prefix=str(addr.parent.prefix),
                tenant=addr.tenant.name if addr.tenant else None,
                uuid=addr.id,
                tags=nautobot.get_tag_strings(addr.tags),
            )
            if self.tenant:
                new_ip.model_flags = DiffSyncModelFlags.SKIP_UNMATCHED_DST
            self.add(new_ip)
            for mapping in IPAddressToInterface.objects.filter(ip_address=addr):
                new_mapping = self.ip_on_intf(
                    address=str(addr.address),
                    device=mapping.interface.device.name,
                    port=mapping.interface.name,
                    primary=len(addr.primary_ip4_for.all()) > 0 or len(addr.primary_ip6_for.all()) > 0,
                    uuid=mapping.id,
                )
                if self.tenant:
                    new_mapping.model_flags = DiffSyncModelFlags.SKIP_UNMATCHED_DST
                self.add(new_mapping)

    def sync_complete(self, source: DiffSync, diff, *args, **kwargs):
        """Label and clean up function for DiffSync sync.

        Once the sync is complete, this function labels all imported objects and then
        deletes any objects from Nautobot that need to be deleted in a specific order.

        Args:
            source: The DiffSync whose data was used to update this instance.
            diff: The Diff calculated prior to the sync operation.
        """
        for grouping in ["addresses", "prefixes", "ports", "devices"]:
            for nautobot_obj in self.objects_to_delete[grouping]:
                try:
                    if self.job.debug:
                        self.job.logger.info(f"Deleting {nautobot_obj}.")
                    nautobot_obj.delete()
                except ProtectedError:
                    self.job.logger.info(f"Deletion failed protected object: {nautobot_obj}")
            self.objects_to_delete[grouping] = []
        return super().sync_complete(source, diff, *args, **kwargs)

    def load(self):
        """Load data from Nautobot into DiffSync models."""
        self.load_sites()
        self.load_devices()
        self.load_ports()
        self.load_prefixes()
        self.load_addresses()
