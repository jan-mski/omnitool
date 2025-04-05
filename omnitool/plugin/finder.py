import logging
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Optional

from omnitool import settings
from omnitool.plugin.base import PluginLocation, PluginModule


PLUGIN_ENTRY_POINT_GROUP = "omnitool.plugin"

logger = logging.getLogger(__name__)


@dataclass
class PluginEntryPoint(PluginModule):
    entry_point: EntryPoint

    @property
    def name(self) -> str:
        return self.entry_point.name

    def load(self) -> None:
        super().load()
        self.entry_point.load()


def find_plugins() -> list[PluginLocation]:
    plugin_modules = _find_plugin_modules()

    installed_plugins : dict[str, PluginModule] = _find_installed_plugins(plugin_modules)
    configuration_dirs : dict[str, Path] = _find_plugin_configuration_dirs(installed_plugins)
    plugin_locations = [PluginLocation(configuration_dir=configuration_dirs[plugin_name],
                                       plugin_module=installed_plugins[plugin_name])
                        for plugin_name in installed_plugins.keys()]

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

    logger.debug(f"Found plugin modules for plugins: {[plugin.name for plugin in plugin_modules]}")

    return plugin_modules


def _find_installed_plugins(plugin_modules: list[PluginModule]) -> dict[str, PluginModule]:
    omnitool_settings = settings.omnitool_settings
    enabled_plugins = omnitool_settings.enabled_builtin_plugins + omnitool_settings.enabled_user_plugins
    plugin_modules_dict = {module.name: module for module in plugin_modules}
    installed_plugins = {}

    for plugin_name in enabled_plugins:
        plugin_module = plugin_modules_dict.get(plugin_name)

        if not plugin_module:
            logger.warning(f"Requested enabled plugin '{plugin_name}' is not installed - skipping")
            continue

        logger.debug(f"Requested enabled plugin '{plugin_name}' is installed")
        installed_plugins[plugin_name] = plugin_module

    return installed_plugins


def _find_plugin_configuration_dirs(installed_plugins: dict[str, PluginModule]) -> dict[str, Path]:
    return {plugin_name: _find_plugin_configuration_dir(plugin_name) for plugin_name in installed_plugins.keys()}


def _find_plugin_configuration_dir(plugin_name: str) -> Optional[Path]:
    plugin_config_dir = settings.PLUGIN_CONFIGURATIONS_PATH / plugin_name

    if plugin_config_dir.exists() and not plugin_config_dir.is_dir():
        logger.warning(f"Plugin configuration path '{plugin_config_dir}' does not point to a directory, ignoring")
        return None

    plugin_config_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Plugin configuration directory for '{plugin_name}' is '{plugin_config_dir}'")

    return plugin_config_dir
