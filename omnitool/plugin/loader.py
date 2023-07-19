import logging
import sys
from importlib.util import spec_from_file_location, module_from_spec
from os.path import splitext
from pathlib import Path
from types import ModuleType
from typing import Dict
from uuid import uuid4

from omnitool.plugin import finder
from omnitool.plugin.configuration import PluginConfigurationService
from omnitool.plugin.finder import PluginLocation
from omnitool.plugin.plugin import Plugin


logger = logging.getLogger(__name__)


def load_plugins():
    plugin_locations = finder.find_plugins()

    if not plugin_locations:
        logger.info("No plugins found.")
        return

    for location in plugin_locations:
        loaded_plugin = _load_plugin(location)
        loaded_plugins[loaded_plugin.name] = loaded_plugin


def _load_plugin(location: PluginLocation) -> Plugin:
    plugin_module = _import_module(location.module_file, _generate_module_name(location.module_file))
    definition = getattr(plugin_module, "plugin")

    try:
        # TODO: could this be constructed in the finder? importing definition would have to be moved to plugin.load()
        configuration_service = PluginConfigurationService(location.configuration_file,
                                                           getattr(definition, "resource_data_type"))
        configuration_service.load_configuration()

        plugin = Plugin(configuration_service, definition, location)

        logger.info(f"Plugin '{plugin.name}' loaded from '{location.root_dir}'.")

        return plugin
    except Exception as e:
        logger.error(f"Failed to load plugin from '{location.root_dir}'.", exc_info=e)


def _import_module(module_file: Path, module_name: str) -> ModuleType:
    spec = spec_from_file_location(module_name, module_file)
    module = module_from_spec(spec)

    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module


def _generate_module_name(module_file: Path) -> str:
    module_dir_name = module_file.parent.name
    module_file_name, _ = splitext(module_file.name)

    clean_module_file_name = module_file_name.replace("\\", "_")

    return f"{module_dir_name}-{clean_module_file_name}-{uuid4()}"


loaded_plugins: Dict[str, Plugin] = {}
