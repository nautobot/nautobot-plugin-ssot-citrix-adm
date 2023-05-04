"""Test the Nautobot CRUD functions for all DiffSync models."""
from unittest.mock import MagicMock
from diffsync import DiffSync
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
        self.diffsync.job.log_info = MagicMock()

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

    def test_update(self):
        """Validate the NautobotDatacenter update() method updates a Site."""
        site = Site.objects.create(name="Test", slug="test", status=Status.objects.get(name="Active"))
        site.validated_save()
        test_dc = NautobotDatacenter(name="Test", region="", latitude="", longitude="", uuid=None)
        test_dc.uuid = site.id
        update_attrs = {
            "latitude": "12.345",
            "longitude": "-67.89",
        }
        actual = NautobotDatacenter.update(self=test_dc, attrs=update_attrs)
        site.refresh_from_db()
        self.assertEqual(str(site.latitude).rstrip("0"), update_attrs["latitude"])
        self.assertEqual(str(site.longitude).rstrip("0"), update_attrs["longitude"])
        self.assertEqual(actual, test_dc)

    def test_delete(self):
        """Validate the NautobotDatacenter delete() method deletes a Site."""
        ds_mock_site = MagicMock(spec=Site)
        ds_mock_site.uuid = "1234567890"
        ds_mock_site.diffsync = MagicMock()
        ds_mock_site.diffsync.objects_to_delete = {"sites": []}
        ds_mock_site.diffsync.job.log_info = MagicMock()
        mock_site = MagicMock(spec=Site)
        mock_site.name = "Test"
        site_get_mock = MagicMock(return_value=mock_site)
        with patch.object(Site.objects, "get", site_get_mock):
            result = NautobotDatacenter.delete(ds_mock_site)
        ds_mock_site.diffsync.job.log_info.assert_called_once_with(message="Deleting Site Test.")
        self.assertEqual(ds_mock_site, result)
        self.assertEqual(len(ds_mock_site.diffsync.objects_to_delete["sites"]), 1)
