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
    def source(self) -> str:
        return str(self.entry_point)

    @property
    def name(self) -> str:
        return self.entry_point.name

    def load(self) -> None:
        super().load()
        self.entry_point.load()


def find_plugins() -> list[PluginLocation]:
    logger.info("Searching for plugins...")

    plugin_modules = _find_plugin_modules()
    installed_plugins = _find_installed_plugins(plugin_modules)
    configuration_dirs = _find_plugin_configuration_dirs(installed_plugins)
    plugin_locations = _create_plugin_locations(configuration_dirs, installed_plugins)

    if plugin_locations:
        logger.info(f"Plugins found: {[location.plugin_name for location in plugin_locations]}")
    else:
        logger.info("No plugins found")

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


def _create_plugin_locations(configuration_dirs: dict[str, Path],
                             installed_plugins: dict[str, PluginModule]) -> list[PluginLocation]:
    plugin_locations = []

    for plugin_name in installed_plugins.keys():
        configuration_dir = configuration_dirs[plugin_name]

        if not _is_configuration_dir_valid(configuration_dir):
            logger.warning(f"Skipping plugin '{plugin_name}' due to invalid configuration directory")
            continue

        plugin_locations.append(PluginLocation(
            configuration_dir=configuration_dir,
            plugin_module=installed_plugins[plugin_name]
        ))

    return plugin_locations


def _find_plugin_configuration_dir(plugin_name: str) -> Optional[Path]:
    configuration_dir = settings.PLUGIN_CONFIGURATIONS_PATH / plugin_name

    if not configuration_dir.exists():
        configuration_dir.mkdir(parents=True)

    logger.debug(f"Plugin configuration directory for '{plugin_name}' is '{configuration_dir}'")

    return configuration_dir


def _is_configuration_dir_valid(configuration_dir: Path) -> bool:
    if configuration_dir.exists() and not configuration_dir.is_dir():
        logger.warning(f"Plugin configuration directory '{configuration_dir}' is not a directory")
        return False

    return True
