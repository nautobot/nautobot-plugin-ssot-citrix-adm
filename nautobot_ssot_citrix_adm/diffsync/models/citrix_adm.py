"""Nautobot SSoT Citrix ADM DiffSync models for Nautobot SSoT Citrix ADM SSoT."""

from nautobot_ssot_citrix_adm.diffsync.models.base import (
    Datacenter,
    Device,
    Port,
    Subnet,
    Address,
    IPAddressOnInterface,
)


class CitrixAdmDatacenter(Datacenter):
    """Citrix ADM implementation of Datacenter DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site in Citrix ADM from Datacenter object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Site in Citrix ADM from Datacenter object."""
        return super().update(attrs)

    def delete(self):
        """Delete Site in Citrix ADM from Datacenter object."""
        return self


class CitrixAdmDevice(Device):
    """Citrix ADM implementation of Device DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Citrix ADM from Device object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Citrix ADM from Device object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Citrix ADM from Device object."""
        return self


class CitrixAdmPort(Port):
    """Citrix ADM implementation of Port DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Interface in Citrix ADM from Port object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Interface in Citrix ADM from Port object."""
        return super().update(attrs)

    def delete(self):
        """Delete Interface in Citrix ADM from Port object."""
        return self


class CitrixAdmSubnet(Subnet):
    """Citrix ADM implementation of Subnet DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Prefix in Citrix ADM from Subnet object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Prefix in Citrix ADM from Subnet object."""
        return super().update(attrs)

    def delete(self):
        """Delete Prefix in Citrix ADM from Subnet object."""
        return self


class CitrixAdmAddress(Address):
    """Citrix ADM implementation of Address DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IP Address in Citrix ADM from Address object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update IP Address in Citrix ADM from Address object."""
        return super().update(attrs)

    def delete(self):
        """Delete IP Address in Citrix ADM from Address object."""
        return self


class CitrixAdmIPAddressOnInterface(IPAddressOnInterface):
    """Citrix ADM implementation of IPAddressOnInterface DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IPAddressToInterface in Citrix ADM from CitrixAdmIPAddressOnInterface object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update IPAddressToInterface in Citrix ADM from CitrixAdmIPAddressOnInterface object."""
        return super().update(attrs)

    def delete(self):
        """Delete IPAddressToInterface in Citrix ADM from CitrixAdmIPAddressOnInterface object."""
        return self
