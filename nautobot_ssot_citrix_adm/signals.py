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
    LocationType = apps.get_model("dcim", "LocationType")
    Device = apps.get_model("dcim", "Device")
    Interface = apps.get_model("dcim", "Interface")
    Prefix = apps.get_model("ipam", "Prefix")
    IPAddress = apps.get_model("ipam", "IPAddress")
    Platform = apps.get_model("dcim", "Platform")

    region = LocationType.objects.update_or_create(name="Region", defaults={"nestable": True})[0]
    site = LocationType.objects.update_or_create(name="Site", defaults={"parent": region})[0]
    site.content_types.add(ContentType.objects.get_for_model(Device))

    citrix_manu, _ = Manufacturer.objects.update_or_create(name="Citrix")
    Platform.objects.update_or_create(
        name="citrix.adc",
        defaults={
            "name": "citrix.adc",
            "napalm_driver": "netscaler",
            "manufacturer": citrix_manu,
            "network_driver": "netscaler",
        },
    )
    ha_node_cf_dict = {
        "key": "ha_node",
        "type": CustomFieldTypeChoices.TYPE_TEXT,
        "label": "HA Node",
    }
    ha_node_field, _ = CustomField.objects.get_or_create(key=ha_node_cf_dict["key"], defaults=ha_node_cf_dict)
    ha_node_field.content_types.add(ContentType.objects.get_for_model(Device))
    os_cf_dict = {
        "key": "os_version",
        "type": CustomFieldTypeChoices.TYPE_TEXT,
        "label": "OS Version",
    }
    ver_field, _ = CustomField.objects.get_or_create(key=os_cf_dict["key"], defaults=os_cf_dict)
    ver_field.content_types.add(ContentType.objects.get_for_model(Device))
    sor_cf_dict = {
        "type": CustomFieldTypeChoices.TYPE_TEXT,
        "key": "system_of_record",
        "label": "System of Record",
    }
    sor_custom_field, _ = CustomField.objects.update_or_create(key=sor_cf_dict["key"], defaults=sor_cf_dict)
    sync_cf_dict = {
        "type": CustomFieldTypeChoices.TYPE_DATE,
        "key": "ssot_last_synchronized",
        "label": "Last sync from System of Record",
    }
    sync_custom_field, _ = CustomField.objects.update_or_create(key=sync_cf_dict["key"], defaults=sync_cf_dict)
    for model in [Device, Interface, Prefix, IPAddress]:
        sor_custom_field.content_types.add(ContentType.objects.get_for_model(model))
        sync_custom_field.content_types.add(ContentType.objects.get_for_model(model))
