"""Signals triggered when Nautobot starts to perform certain actions."""


def nautobot_database_ready_callback(sender, *, apps, **kwargs):  # pylint: disable=unused-argument
    """Ensure the Citrix Manufacturer is in place for DeviceTypes to use.

    Callback function triggered by the nautobot_database_ready signal when the Nautobot database is fully ready.
    """
    Manufacturer = apps.get_model("dcim", "Manufacturer")  # pylint: disable=invalid-name

    _, _ = Manufacturer.objects.update_or_create(name="Citrix", slug="citrix")
