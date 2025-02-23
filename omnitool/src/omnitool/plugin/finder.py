import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List


BUILTIN_PLUGINS_RELATIVE_PATH = "plugin/builtin"
USER_PLUGINS_RELATIVE_PATH = ".omnitool/plugins"
PLUGIN_MODULE_FILE_NAME = "plugin.py"
PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"

logger = logging.getLogger(__name__)


@dataclass
class PluginLocation:
    root_dir: Path
    module_file: Path
    configuration_file: Path


def find_plugins(app_root_dir: Path) -> List[PluginLocation]:
    possible_builtin_plugin_dir = app_root_dir / BUILTIN_PLUGINS_RELATIVE_PATH
    possible_user_plugin_dir = Path.home() / USER_PLUGINS_RELATIVE_PATH

    builtin_plugins = _find_plugins(possible_builtin_plugin_dir)
    user_plugins = _find_plugins(possible_user_plugin_dir)

    return builtin_plugins + user_plugins


def _find_plugins(possible_plugin_dir: Path):
    plugin_locations = []

    if not possible_plugin_dir.exists():
        logger.info(f"Directory does not exist: '{possible_plugin_dir}' - creating.")
        possible_plugin_dir.mkdir(parents=True)

        return plugin_locations

    for possible_plugin_dir in possible_plugin_dir.iterdir():
        plugin_location = _find_plugin(possible_plugin_dir)

        if plugin_location:
            plugin_locations.append(plugin_location)

    return plugin_locations


def _find_plugin(possible_plugin_dir: Path) -> PluginLocation | None:
    if not possible_plugin_dir.is_dir():
        logger.info(f"Not a valid plugin directory: '{possible_plugin_dir}': not a directory.")
        return

    module_file = possible_plugin_dir / PLUGIN_MODULE_FILE_NAME
    if not module_file.exists():
        logger.info(f"Not a valid plugin directory: '{possible_plugin_dir}': missing module file.")
        return

    configuration_file = possible_plugin_dir / PLUGIN_CONFIGURATION_FILE_NAME
    if not configuration_file.exists():
        logger.info(f"Not a valid plugin directory: '{possible_plugin_dir}': missing configuration file.")
        return

    return PluginLocation(
        root_dir=possible_plugin_dir,
        module_file=module_file,
        configuration_file=configuration_file
    )
