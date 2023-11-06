"""Test the Nautobot CRUD functions for all DiffSync models."""
from unittest.mock import MagicMock
from diffsync import DiffSync
from django.test import override_settings
from nautobot.dcim.models import Region, Site
from nautobot.extras.models import Status
from nautobot.utilities.testing import TransactionTestCase

from nautobot_ssot_citrix_adm.diffsync.models.nautobot import NautobotDatacenter


class TestNautobotDatacenter(TransactionTestCase):
    """Test the NautobotDatacenter class."""

    def setUp(self):
        """Configure shared objects."""
        super().setUp()
        self.diffsync = DiffSync()
        self.diffsync.job = MagicMock()
        self.diffsync.job.log_warning = MagicMock()
        self.test_dc = NautobotDatacenter(name="Test", region="", latitude="", longitude="", uuid=None)

    def test_create(self):
        """Validate the NautobotDatacenter create() method creates a Site."""
        ids = {"name": "HQ", "region": "NY"}
        attrs = {"latitude": "12.345", "longitude": "-67.89"}
        result = NautobotDatacenter.create(self.diffsync, ids, attrs)
        self.assertIsInstance(result, NautobotDatacenter)
        site_obj = Site.objects.get(name=ids["name"])
        ny_region = Region.objects.get(name=ids["region"])
        self.assertEqual(site_obj.region, ny_region)
        self.assertEqual(str(site_obj.latitude).rstrip("0"), attrs["latitude"])
        self.assertEqual(str(site_obj.longitude).rstrip("0"), attrs["longitude"])

    def test_create_with_duplicate_site(self):
        """Validate the NautobotDatacenter create() method handling of duplicate Site."""
        _, _ = Site.objects.get_or_create(name="HQ")
        ids = {"name": "HQ", "region": ""}
        attrs = {}
        NautobotDatacenter.create(self.diffsync, ids, attrs)
        self.diffsync.job.log_warning.assert_called_with(message="Site HQ already exists so skipping creation.")

    @override_settings(PLUGINS_CONFIG={"nautobot_ssot_citrix_adm": {"update_sites": True}})
    def test_update(self):
        """Validate the NautobotDatacenter update() method updates a Site."""
        site = Site.objects.create(name="Test", slug="test", status=Status.objects.get(name="Active"))
        site.validated_save()
        self.test_dc.uuid = site.id
        update_attrs = {
            "latitude": "12.345",
            "longitude": "-67.89",
        }
        actual = NautobotDatacenter.update(self=self.test_dc, attrs=update_attrs)
        site.refresh_from_db()
        self.assertEqual(str(site.latitude).rstrip("0"), update_attrs["latitude"])
        self.assertEqual(str(site.longitude).rstrip("0"), update_attrs["longitude"])
        self.assertEqual(actual, self.test_dc)

    @override_settings(PLUGINS_CONFIG={"nautobot_ssot_citrix_adm": {"update_sites": False}})
    def test_update_setting_disabled(self):
        """Validate the NautobotDatacenter update() method doesn't update a Site if setting is False."""
        self.test_dc.diffsync = MagicMock()
        self.test_dc.diffsync.job = MagicMock()
        self.test_dc.diffsync.job.log_warning = MagicMock()
        NautobotDatacenter.update(self=self.test_dc, attrs={})
        self.test_dc.diffsync.job.log_warning.assert_called_once_with(
            message="Update sites setting is disabled so skipping updating Test."
        )
