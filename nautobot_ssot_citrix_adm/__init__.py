"""Plugin declaration for nautobot_ssot_citrix_adm."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata
from nautobot.core.signals import nautobot_database_ready
from nautobot.extras.plugins import PluginConfig
from nautobot_ssot_citrix_adm.signals import nautobot_database_ready_callback

__version__ = metadata.version(__name__)


class NautobotSsotCitrixAdmConfig(PluginConfig):
    """Plugin configuration for the nautobot_ssot_citrix_adm plugin."""

    name = "nautobot_ssot_citrix_adm"
    verbose_name = "Nautobot SSoT Citrix ADM"
    version = __version__
    author = "Justin Drew"
    description = "Nautobot SSoT Citrix ADM."
    base_url = "ssot-citrix-adm"
    required_settings = ["base_url", "username", "password", "verify"]
    min_version = "2.1.0"
    max_version = "2.9999"
    default_settings = {"update_sites": True, "hostname_mapping": []}
    caching_config = {}

    def ready(self):
        """Trigger callback when database is ready."""
        super().ready()

        nautobot_database_ready.connect(nautobot_database_ready_callback, sender=self)


config = NautobotSsotCitrixAdmConfig  # pylint:disable=invalid-name
