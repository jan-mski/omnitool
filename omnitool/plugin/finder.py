import logging
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points

from omnitool import settings
from omnitool.plugin.base import PluginLocation, PluginModule, PluginDefinition


PLUGIN_ENTRY_POINT_GROUP = "omnitool.plugin"

logger = logging.getLogger(__name__)


@dataclass
class PluginEntryPoint(PluginModule):
    entry_point: EntryPoint

    @property
    def source(self) -> str:
        return str(self.entry_point)

    @property
    def name(self) -> str:
        return self.entry_point.name

    def load(self) -> PluginDefinition:
        super().load()
        return self.entry_point.load()


def find_plugins() -> list[PluginLocation]:
    logger.debug("Searching for plugins...")

    plugin_modules = _find_plugin_modules()
    installed_plugins = _find_installed_plugins(plugin_modules)
    plugin_locations = _create_plugin_locations(installed_plugins)

    if plugin_locations:
        logger.debug(f"Plugins found: {[location.plugin_name for location in plugin_locations]}")
    else:
        logger.debug("No plugins found")

    return plugin_locations


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


def _create_plugin_locations(installed_plugins: dict[str, PluginModule]) -> list[PluginLocation]:
    return [
        PluginLocation(plugin_module=plugin_module)
        for plugin_name, plugin_module in installed_plugins.items()
    ]
