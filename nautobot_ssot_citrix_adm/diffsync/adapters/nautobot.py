"""Nautobot Adapter for Citrix ADM SSoT plugin."""

from collections import defaultdict
from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from django.db.models import ProtectedError
from nautobot.dcim.models import Device as OrmDevice
from nautobot.dcim.models import Interface, Site
from nautobot.extras.models import Job, Relationship, RelationshipAssociation
from nautobot.ipam.models import IPAddress
from nautobot_ssot_citrix_adm.diffsync.models.nautobot import (
    NautobotAddress,
    NautobotDatacenter,
    NautobotDevice,
    NautobotPort,
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
    address = NautobotAddress

    top_level = ["datacenter", "device", "address"]

    def __init__(self, *args, job: Job, sync=None, **kwargs):
        """Initialize Nautobot.

        Args:
            job (Job): Nautobot job.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.objects_to_delete = defaultdict(list)

    def load_sites(self):
        """Load Sites from Nautobot into DiffSync models."""
        for site in Site.objects.all():
            self.job.log_info(message=f"Loading Site {site.name} from Nautobot.")
            new_dc = self.datacenter(
                name=site.name,
                region=site.region.name if site.region else "",
                latitude=str(site.latitude).rstrip("0"),
                longitude=str(site.longitude).rstrip("0"),
                uuid=site.id,
            )
            self.add(new_dc)

    def load_devices(self):
        """Load Devices from Nautobot into DiffSync models."""
        for dev in OrmDevice.objects.select_related("device_type", "site", "status").filter(
            _custom_field_data__system_of_record="Citrix ADM"
        ):
            self.job.log_info(message=f"Loading Device {dev.name} from Nautobot.")
            version = dev._custom_field_data["os_version"]
            if LIFECYCLE_MGMT:
                try:
                    software_relation = Relationship.objects.get(slug="device_soft")
                    relationship = RelationshipAssociation.objects.get(
                        relationship=software_relation, destination_id=dev.id
                    )
                    version = relationship.source.version
                except RelationshipAssociation.DoesNotExist:
                    self.job.log_info(message=f"Unable to find DLC Software version for {dev.name}.")
                    version = ""
            new_dev = self.device(
                name=dev.name,
                model=dev.device_type.model,
                role=dev.device_role.name,
                serial=dev.serial,
                site=dev.site.name,
                status=dev.status.name,
                tenant=dev.tenant.name if dev.tenant else "",
                version=version,
                uuid=dev.id,
            )
            self.add(new_dev)

    def load_ports(self):
        """Load Interfaces from Nautobot into DiffSync models."""
        for intf in Interface.objects.select_related("device", "status").filter(
            device___custom_field_data__system_of_record="Citrix ADM"
        ):
            try:
                dev = self.get(self.device, intf.device.name)
                new_intf = self.port(
                    name=intf.name,
                    device=intf.device.name,
                    status=intf.status.name,
                    description=intf.description,
                    uuid=intf.id,
                )
                self.add(new_intf)
                dev.add_child(new_intf)
            except ObjectNotFound:
                self.job.log_warning(
                    message=f"Unable to find {intf.device.name} loaded so skipping loading port {intf.name}."
                )

    def load_addresses(self):
        """Load IP Addresses from Nautobot into DiffSync models."""
        for addr in IPAddress.objects.filter(_custom_field_data__system_of_record="Citrix ADM"):
            if addr.family == 4:
                primary = hasattr(addr, "primary_ip4_for")
            else:
                primary = hasattr(addr, "primary_ip6_for")
            new_ip = self.address(
                address=str(addr.address),
                device=addr.assigned_object.device.name if addr.assigned_object else "",
                port=addr.assigned_object.name if addr.assigned_object else "",
                primary=primary,
                tenant=addr.tenant.name if addr.tenant else "",
                uuid=addr.id,
                tags=nautobot.get_tag_strings(addr.tags),
            )
            self.add(new_ip)

    def sync_complete(self, source: DiffSync, diff, *args, **kwargs):
        """Label and clean up function for DiffSync sync.

        Once the sync is complete, this function labels all imported objects and then
        deletes any objects from Nautobot that need to be deleted in a specific order.

        Args:
            source: The DiffSync whose data was used to update this instance.
            diff: The Diff calculated prior to the sync operation.
        """
        self.job.log_info(message="Sync is complete. Labelling imported objects from Citrix ADM.")
        source.label_imported_objects(target=self)

        for grouping in ["addresses", "ports", "devices"]:
            for nautobot_obj in self.objects_to_delete[grouping]:
                try:
                    self.job.log_info(message=f"Deleting {nautobot_obj}.")
                    nautobot_obj.delete()
                except ProtectedError:
                    self.job.log_info(message=f"Deletion failed protected object: {nautobot_obj}")
            self.objects_to_delete[grouping] = []
        return super().sync_complete(source, diff, *args, **kwargs)

    def load(self):
        """Load data from Nautobot into DiffSync models."""
        self.load_sites()
        self.load_devices()
        self.load_ports()
        self.load_addresses()
