import logging
import inspect
from dataclasses import dataclass
from typing import Any, Optional

from omnitool.plugin.api.operation import OperationFunction
from omnitool.plugin.loading import finder
from omnitool.plugin.loading.configuration import load_configuration, PluginConfiguration
from omnitool.plugin.loading.data import load_data, PluginData
from omnitool.plugin.api.definition import PluginDefinition
from omnitool.plugin.loading.location import PluginModule


logger = logging.getLogger(__name__)

loaded_plugins: dict[str, "LoadedPlugin"] = {}


@dataclass
class LoadedPlugin:
    """
    Represents a loaded plugin.
    """

    data: PluginData
    definition: PluginDefinition
    module: PluginModule

    @property
    def name(self) -> str:
        return self.module.name


def load_plugins() -> None:
    """
    Finds and loads all available plugins.
    """
    global loaded_plugins
    loaded_plugins = {}

    plugin_modules: list[PluginModule] = finder.find_plugins()

    if not plugin_modules:
        logger.debug("No plugins available to load")
        return

    logger.debug("Loading plugins...")

    for plugin_module in plugin_modules:
        try:
            loaded_plugin: LoadedPlugin = _load_plugin(plugin_module)

            if loaded_plugin:
                loaded_plugins[loaded_plugin.name] = loaded_plugin
                logger.debug(f"LoadedPlugin '{loaded_plugin.name}' loaded from '{plugin_module.source}'")
        except Exception as e:
            logger.debug(f"Failed to load plugin '{plugin_module.name}' from {plugin_module.source}", exc_info=e)

    logger.debug(f"Plugins loaded: {list(loaded_plugins.keys())}")


def _load_plugin(plugin_module: PluginModule) -> LoadedPlugin:
    plugin_definition: PluginDefinition = _load_definition(plugin_module)
    plugin_configuration: PluginConfiguration = load_configuration(plugin_module.name)
    plugin_data: PluginData = load_data(plugin_module.name, plugin_configuration, plugin_definition)

    return LoadedPlugin(data=plugin_data, definition=plugin_definition, module=plugin_module)


def _load_definition(plugin_module: PluginModule) -> PluginDefinition:
    plugin_definition: PluginDefinition = plugin_module.load()
    _validate_definition(plugin_definition)

    return plugin_definition


def _validate_definition(plugin_definition: Any) -> None:
    if not isinstance(plugin_definition, PluginDefinition):
        raise ValueError("LoadedPlugin definition must be of type PluginDefinition")
    if plugin_definition.operations and not plugin_definition.resource_data_type:
        raise ValueError("LoadedPlugin resource_data_type must be defined when operations are present")
    if plugin_definition.resource_data_type and not plugin_definition.context_loader_function:
        raise ValueError("LoadedPlugin context_loader_function must be defined when resource_data_type is present")
    _validate_operations(plugin_definition.operations)


def _validate_operations(operations: list[OperationFunction]) -> None:
    for operation in operations:
        if not callable(operation):
            raise ValueError(f"Operation {operation} must be a callable function")
        
        try:
            signature = inspect.signature(operation)
            if "context" not in signature.parameters:
                raise ValueError(f"Operation {operation.__name__} must have a 'context' parameter")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Cannot inspect operation {operation}: {e}")
