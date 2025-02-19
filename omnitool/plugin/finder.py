import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


RELATIVE_BUILTIN_PLUGINS_DIR = "plugin/builtin"
RELATIVE_USER_PLUGINS_DIR = ".omnitool/plugins"
PLUGIN_MODULE_FILE_NAME = "plugin.py"
PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"


logger = logging.getLogger(__name__)


@dataclass
class PluginLocation:
    root_dir: Path
    module_file: Path
    configuration_file: Path


def find_plugins(app_root_dir: Path) -> List[PluginLocation]:
    maybe_builtin_plugin_dir = app_root_dir / RELATIVE_BUILTIN_PLUGINS_DIR
    maybe_user_plugin_dir = Path.home() / RELATIVE_USER_PLUGINS_DIR

    builtin_plugins = _find_plugins(maybe_builtin_plugin_dir)
    user_plugins = _find_plugins(maybe_user_plugin_dir)

    return builtin_plugins + user_plugins


def _find_plugins(maybe_plugin_dir):
    plugin_locations = []

    if not maybe_plugin_dir.exists():
        logger.info(f"No plugins found in directory: '{maybe_plugin_dir}'.")
        maybe_plugin_dir.mkdir(parents=True)

        return plugin_locations

    for maybe_plugin_dir in maybe_plugin_dir.iterdir():
        plugin_files = _find_plugin_files(maybe_plugin_dir)

        if plugin_files:
            module_file = plugin_files[0]
            configuration_file = plugin_files[1]

            plugin_locations.append(PluginLocation(
                root_dir=maybe_plugin_dir,
                module_file=module_file,
                configuration_file=configuration_file
            ))

    return plugin_locations


def _find_plugin_files(plugin_dir: Path) -> Tuple[Path, Path] | None:
    if not plugin_dir.is_dir():
        logger.info(f"Not a valid plugin directory: '{plugin_dir}': not a directory.")
        return

    module_file = plugin_dir / PLUGIN_MODULE_FILE_NAME
    if not module_file.exists():
        logger.info(f"Not a valid plugin directory: '{plugin_dir}': missing module file.")
        return

    configuration_file = plugin_dir / PLUGIN_CONFIGURATION_FILE_NAME
    if not configuration_file.exists():
        logger.info(f"Not a valid plugin directory: '{plugin_dir}': missing configuration file.")
        return

    return module_file, configuration_file
