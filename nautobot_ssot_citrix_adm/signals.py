"""Signals triggered when Nautobot starts to perform certain actions."""
from nautobot.extras.choices import CustomFieldTypeChoices


def nautobot_database_ready_callback(sender, *, apps, **kwargs):  # pylint: disable=unused-argument
    """Ensure the Citrix Manufacturer is in place for DeviceTypes to use. Adds OS Version CustomField to Devices and System of Record and Last Sync'd to Site, Device, Interface, and IPAddress.

    Callback function triggered by the nautobot_database_ready signal when the Nautobot database is fully ready.
    """
    # pylint: disable=invalid-name, too-many-locals
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    Manufacturer = apps.get_model("dcim", "Manufacturer")
    Device = apps.get_model("dcim", "Device")
    Interface = apps.get_model("dcim", "Interface")
    IPAddress = apps.get_model("ipam", "IPAddress")
    Platform = apps.get_model("dcim", "Platform")

    citrix_manu, _ = Manufacturer.objects.update_or_create(name="Citrix", slug="citrix")
    Platform.objects.update_or_create(name="citrix.adc", slug="netscaler", napalm_driver="netscaler", manufacturer=citrix_manu)

    os_cf_dict = {
        "name": "os_version",
        "slug": "os_version",
        "type": CustomFieldTypeChoices.TYPE_TEXT,
        "label": "OS Version",
    }
    ver_field, _ = CustomField.objects.get_or_create(name=os_cf_dict["name"], defaults=os_cf_dict)
    ver_field.content_types.add(ContentType.objects.get_for_model(Device))
    sor_cf_dict = {
        "type": CustomFieldTypeChoices.TYPE_TEXT,
        "name": "system_of_record",
        "slug": "system_of_record",
        "label": "System of Record",
    }
    sor_custom_field, _ = CustomField.objects.update_or_create(name=sor_cf_dict["name"], defaults=sor_cf_dict)
    sync_cf_dict = {
        "type": CustomFieldTypeChoices.TYPE_DATE,
        "name": "ssot_last_synchronized",
        "slug": "ssot_last_synchronized",
        "label": "Last sync from System of Record",
    }
    sync_custom_field, _ = CustomField.objects.update_or_create(name=sync_cf_dict["name"], defaults=sync_cf_dict)
    for model in [Device, Interface, IPAddress]:
        sor_custom_field.content_types.add(ContentType.objects.get_for_model(model))
        sync_custom_field.content_types.add(ContentType.objects.get_for_model(model))
