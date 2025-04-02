import logging
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import List, Optional

from omnitool import settings
from omnitool.plugin.base import PluginLocation, PluginModule


PLUGIN_ENTRY_POINT_GROUP = "omnitool.plugin"
PLUGIN_CONFIGURATIONS_PATH = settings.OMNITOOL_HOME_PATH / "plugins"
PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"

logger = logging.getLogger(__name__)


@dataclass
class PluginEntryPoint(PluginModule):
    entry_point: EntryPoint

    @property
    def name(self) -> str:
        return self.entry_point.name

    def load(self):
        super().load()
        self.entry_point.load()


def find_plugins() -> List[PluginLocation]:
    plugin_modules = _find_plugin_modules()
    omnitool_settings = settings.omnitool_settings

    builtin_plugin_locations = _find_plugin_locations(plugin_modules, omnitool_settings.enabled_builtin_plugins)
    user_plugin_locations = _find_plugin_locations(plugin_modules, omnitool_settings.enabled_user_plugins)

    return builtin_plugin_locations + user_plugin_locations


def _find_plugin_modules() -> List[PluginModule]:
    return [PluginEntryPoint(entry_point) for entry_point in entry_points(group=PLUGIN_ENTRY_POINT_GROUP)]


def _find_plugin_locations(plugin_modules: list[PluginModule], plugin_names: list[str]) -> List[PluginLocation]:
    locations = []
    plugin_modules_dict = {module.name: module for module in plugin_modules}

    for plugin_name in plugin_names:
        plugin_module = plugin_modules_dict.get(plugin_name)

        if not plugin_module:
            logger.warning(f"Requested enabled plugin '{plugin_name}' is not installed - skipping")
            continue

        configuration_file = _find_plugin_configuration(plugin_name)
        locations.append(PluginLocation(configuration_file, plugin_module))

    return locations


def _find_plugin_configuration(plugin_name: str) -> Optional[Path]:
    plugin_config_dir = PLUGIN_CONFIGURATIONS_PATH / plugin_name

    if plugin_config_dir.exists() and not plugin_config_dir.is_dir():
        logger.warning(f"Plugin configuration path '{plugin_config_dir}' does not point to a directory")
        return None

    plugin_config_dir.mkdir(parents=True, exist_ok=True)
    config_file = plugin_config_dir / PLUGIN_CONFIGURATION_FILE_NAME

    if config_file.exists() and not config_file.is_file():
        logger.warning(f"Plugin configuration path '{config_file}' does not point to a file")
        return None

    if not config_file.exists():
        config_file.write_text("{}", encoding="utf-8")

    return config_file
