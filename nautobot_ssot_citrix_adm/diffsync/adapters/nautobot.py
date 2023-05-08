"""Nautobot Adapter for Citrix ADM SSoT plugin."""

from collections import defaultdict
from django.db.models import ProtectedError
from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound
from nautobot.dcim.models import Device as OrmDevice, Interface, Site
from nautobot.extras.models import Job
from nautobot.ipam.models import IPAddress
from nautobot_ssot_citrix_adm.diffsync.models.nautobot import (
    NautobotDatacenter,
    NautobotDevice,
    NautobotPort,
    NautobotAddress,
)


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
        for dev in OrmDevice.objects.all():
            self.job.log_info(message=f"Loading Device {dev.name} from Nautobot.")
            new_dev = self.device(
                name=dev.name,
                model=dev.device_type.model,
                serial=dev.serial,
                site=dev.site.name,
                status=dev.status.name,
                version=dev._custom_field_data["os_version"],
                uuid=dev.id,
            )
            self.add(new_dev)

    def load_ports(self):
        """Load Interfaces from Nautobot into DiffSync models."""
        for intf in Interface.objects.all():
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
        for addr in IPAddress.objects.all():
            if addr.family == 4:
                primary = hasattr(addr, "primary_ip4_for")
            else:
                primary = hasattr(addr, "primary_ip6_for")
            new_ip = self.address(
                address=str(addr.address),
                device=addr.assigned_object.device.name if addr.assigned_object else "",
                port=addr.assigned_object.name if addr.assigned_object else "",
                primary=primary,
                uuid=addr.id,
            )
            self.add(new_ip)

    def sync_complete(self, source: DiffSync, *args, **kwargs):
        """Label and clean up function for DiffSync sync.

        Once the sync is complete, this function labels all imported objects and then
        deletes any objects from Nautobot that need to be deleted in a specific order.

        Args:
            source (DiffSync): DiffSync
        """
        self.job.log_info(message="Sync is complete. Labelling imported objects from Citrix ADM.")
        source.label_imported_objects(target=self)

        for grouping in ["sites"]:
            for nautobot_obj in self.objects_to_delete[grouping]:
                try:
                    self.job.log_info(message=f"Deleting {nautobot_obj}.")
                    nautobot_obj.delete()
                except ProtectedError:
                    self.job.log_info(message=f"Deletion failed protected object: {nautobot_obj}")
            self.objects_to_delete[grouping] = []
        return super().sync_complete(source, *args, **kwargs)

    def load(self):
        """Load data from Nautobot into DiffSync models."""
        self.load_sites()
        self.load_devices()
        self.load_ports()
        self.load_addresses()
