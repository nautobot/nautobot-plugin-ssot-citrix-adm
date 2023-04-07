"""Plugin declaration for nautobot_ssot_citrix_adm."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)

from nautobot.extras.plugins import PluginConfig


class NautobotSsotCitrixAdmConfig(PluginConfig):
    """Plugin configuration for the nautobot_ssot_citrix_adm plugin."""

    name = "nautobot_ssot_citrix_adm"
    verbose_name = "Nautobot SSoT Citrix ADM"
    version = __version__
    author = "Justin Drew"
    description = "Nautobot SSoT Citrix ADM."
    base_url = "ssot-citrix-adm"
    required_settings = []
    min_version = "1.5.0"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}


config = NautobotSsotCitrixAdmConfig  # pylint:disable=invalid-name
