"""Nautobot SSoT Citrix ADM DiffSync models for Nautobot SSoT Citrix ADM SSoT."""

from nautobot_ssot_citrix_adm.diffsync.models.base import Device


class CitrixAdmDevice(Device):
    """Citrix ADM implementation of Device DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Citrix ADM from NautobotSsotCitrixAdmDevice object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Citrix ADM from NautobotSsotCitrixAdmDevice object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Citrix ADM from NautobotSsotCitrixAdmDevice object."""
        return self
