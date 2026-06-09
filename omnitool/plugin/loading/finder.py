import logging
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points

from omnitool import settings
from omnitool.plugin.api.definition import PluginDefinition
from omnitool.plugin.loading.location import PluginModule


PLUGIN_ENTRY_POINT_GROUP = "omnitool.plugin"

logger = logging.getLogger(__name__)


@dataclass
class PluginEntryPoint(PluginModule):
    """
    Represents a plugin entry point.
    """
    entry_point: EntryPoint

    @property
    def source(self) -> str:
        return str(self.entry_point)

    @property
    def name(self) -> str:
        return self.entry_point.name

    def load(self) -> PluginDefinition:
        return self.entry_point.load()


def find_plugins() -> list[PluginModule]:
    """
    Finds all available plugins.
    """
    logger.debug("Searching for plugins...")

    plugin_modules = _find_plugin_modules()
    installed_plugins = _find_installed_plugins(plugin_modules)

    if installed_plugins:
        logger.debug(f"Plugins found: {list(installed_plugins.keys())}")
    else:
        logger.debug("No plugins found")

    return list(installed_plugins.values())


def _find_plugin_modules() -> list[PluginModule]:
    seen_names = set()
    plugin_modules = []

    for entry_point in entry_points(group=PLUGIN_ENTRY_POINT_GROUP):
        if entry_point.name in seen_names:
            logger.debug(f"Skipping duplicate plugin entry point '{entry_point.name}'")
        else:
            plugin_modules.append(PluginEntryPoint(entry_point))
            seen_names.add(entry_point.name)

    logger.debug(f"Found plugin modules for plugins: {[module.name for module in plugin_modules]}")

    return plugin_modules


def _find_installed_plugins(plugin_modules: list[PluginModule]) -> dict[str, PluginModule]:
    omnitool_settings = settings.omnitool_settings
    enabled_plugins = omnitool_settings.enabled_builtin_plugins + omnitool_settings.enabled_user_plugins
    plugin_modules_dict = {module.name: module for module in plugin_modules}
    installed_plugins = {}

    for plugin_name in enabled_plugins:
        plugin_module = plugin_modules_dict.get(plugin_name)

        if not plugin_module:
            logger.debug(f"Requested enabled plugin '{plugin_name}' is not installed - skipping")
            continue

        logger.debug(f"Requested enabled plugin '{plugin_name}' is installed")
        installed_plugins[plugin_name] = plugin_module

    return installed_plugins


