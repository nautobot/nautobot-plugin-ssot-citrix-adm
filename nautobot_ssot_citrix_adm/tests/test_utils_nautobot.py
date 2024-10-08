"""Tests to validate utility functions for Nautobot."""

import sys
from unittest import skip
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from nautobot.core.testing import TransactionTestCase
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer, Platform
from nautobot.extras.models import Relationship, RelationshipAssociation, Role, Status
from nautobot_device_lifecycle_mgmt.models import SoftwareLCM

from nautobot_ssot_citrix_adm.utils.nautobot import add_software_lcm, assign_version_to_device


class TestUtilsNautobot(TransactionTestCase):  # pylint: disable=too-many-instance-attributes
    """Test Nautobot utility functions."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Setup shared objects for testing."""
        super().setUp()
        self.active_status = Status.objects.get(name="Active")
        self.site, _ = Location.objects.get_or_create(
            name="DC1", location_type=LocationType.objects.get(name="Site"), status=self.active_status
        )
        self.platform, _ = Platform.objects.get_or_create(name="Test")
        self.manufacturer = Manufacturer.objects.get(name="Citrix")
        self.device_type, _ = DeviceType.objects.get_or_create(model="SDX", manufacturer=self.manufacturer)
        self.device_role, _ = Role.objects.get_or_create(name="test")
        self.device, _ = Device.objects.get_or_create(
            name="Test",
            role=self.device_role,
            device_type=self.device_type,
            location=self.site,
            status=self.active_status,
        )
        self.software_lcm, _ = SoftwareLCM.objects.get_or_create(version="1.0", device_platform=self.platform)
        self.diffsync = MagicMock()
        self.diffsync.job.logger.info = MagicMock()

    def test_add_software_lcm_existing_version(self):
        """Test the add_software_lcm() function with an existing version."""
        version = "1.0"
        result = add_software_lcm(self.diffsync, self.platform.name, version)
        self.assertEqual(result, self.software_lcm.id)
        self.diffsync.job.logger.info.assert_not_called()

    def test_add_software_lcm_new_version(self):
        """Test the add_software_lcm() function with a new version."""
        version = "2.0"
        result = add_software_lcm(self.diffsync, self.platform.name, version)
        soft_lcm = SoftwareLCM.objects.get(device_platform=self.platform, version=version)
        self.assertEqual(result, soft_lcm.id)
        self.diffsync.job.logger.info.assert_called_once_with("Creating Version 2.0 for Test.")

    def test_assign_version_to_device_new_relationship(self):
        """Test the assign_version_to_device() function with a new Relationship."""
        assign_version_to_device(self.diffsync, self.device, self.software_lcm.id)
        relationship = Relationship.objects.get(label="Software on Device")
        association = RelationshipAssociation.objects.get(relationship=relationship, destination_id=self.device.id)
        self.assertEqual(association.source_type, ContentType.objects.get_for_model(SoftwareLCM))
        self.assertEqual(association.source_id, self.software_lcm.id)
        self.assertEqual(association.destination_type, ContentType.objects.get_for_model(Device))
        self.assertEqual(association.destination_id, self.device.id)

    def test_assign_version_to_device_existing_relationship(self):
        """Test the assign_version_to_device() function when Device already has a RelationshipAssociation."""
        self.diffsync.job.logger.warning = MagicMock()
        assign_version_to_device(self.diffsync, self.device, self.software_lcm.id)
        version = "3.0"
        result = add_software_lcm(self.diffsync, self.platform.name, version)
        assign_version_to_device(self.diffsync, self.device, result)
        relationship = Relationship.objects.get(label="Software on Device")
        association = RelationshipAssociation.objects.get(relationship=relationship, destination_id=self.device.id)
        self.assertEqual(association.source_type, ContentType.objects.get_for_model(SoftwareLCM))
        self.assertEqual(association.source_id, result)
        self.assertEqual(association.destination_type, ContentType.objects.get_for_model(Device))
        self.assertEqual(association.destination_id, self.device.id)
        self.diffsync.job.logger.warning.assert_called_once_with(
            "Deleting Software Version Relationships for Test to assign a new version."
        )

    @skip("TODO")
    def test_device_lifecycle_management_import_fails(self):
        """Validate that the LIFECYCLE_MGMT variable is set to False if DLC module can't be imported."""
        sys.path = []
        with self.assertRaises(ImportError):
            from nautobot_device_lifecycle_mgmt.models import (  # noqa: F401, pylint: disable=redefined-outer-name,reimported,import-outside-toplevel,unused-import
                SoftwareLCM,
            )

            from nautobot_ssot_citrix_adm.utils.nautobot import (  # pylint: disable=import-outside-toplevel
                LIFECYCLE_MGMT,
            )
        self.assertFalse(LIFECYCLE_MGMT)
