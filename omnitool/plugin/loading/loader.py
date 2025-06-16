import logging
from dataclasses import dataclass

from omnitool.plugin.loading import finder
from omnitool.plugin.loading.configuration import load_configuration, PluginConfiguration
from omnitool.plugin.loading.data import load_data, PluginData
from omnitool.plugin.api.definition import PluginDefinition
from omnitool.plugin.loading.location import PluginLocation


logger = logging.getLogger(__name__)

loaded_plugins: dict[str, "LoadedPlugin"] = {}


@dataclass
class LoadedPlugin:
    """
    Represents a loaded plugin.
    """
    data: PluginData
    definition: PluginDefinition
    location: PluginLocation

    @property
    def name(self) -> str:
        return self.location.plugin_name


def load_plugins() -> None:
    """
    Finds and loads all available plugins.
    """
    global loaded_plugins
    loaded_plugins = {}

    plugin_locations: list[PluginLocation] = finder.find_plugins()

    if not plugin_locations:
        logger.debug("No plugins available to load")
        return

    logger.debug("Loading plugins...")

    for plugin_location in plugin_locations:
        try:
            loaded_plugin: LoadedPlugin = _load_plugin(plugin_location)

            if loaded_plugin:
                loaded_plugins[loaded_plugin.name] = loaded_plugin
                logger.debug(f"LoadedPlugin '{loaded_plugin.name}' loaded from '{plugin_location.plugin_module.source}'")
        except Exception as e:
            logger.debug(f"Failed to load plugin '{plugin_location.plugin_name}' "
                         f"from {plugin_location.plugin_module.source}", exc_info=e)

    logger.debug(f"Plugins loaded: {list(loaded_plugins.keys())}")


def _load_plugin(plugin_location: PluginLocation) -> LoadedPlugin:
    plugin_definition: PluginDefinition = _load_definition(plugin_location)
    plugin_configuration: PluginConfiguration = load_configuration(plugin_location.plugin_name)
    plugin_data: PluginData = load_data(plugin_location.plugin_name, plugin_configuration, plugin_definition)

    return LoadedPlugin(data=plugin_data, definition=plugin_definition, location=plugin_location)


def _load_definition(plugin_location: PluginLocation) -> PluginDefinition:
    plugin_definition: PluginDefinition = plugin_location.load_module()
    _validate_definition(plugin_definition)

    return plugin_definition


def _validate_definition(plugin_definition: PluginDefinition) -> None:
    if not isinstance(plugin_definition, PluginDefinition):
        raise ValueError("LoadedPlugin definition must be of type PluginDefinition")
    if plugin_definition.operations and not plugin_definition.resource_data_type:
        raise ValueError("LoadedPlugin resource_data_type must be defined when operations are present")
    if plugin_definition.resource_data_type and not plugin_definition.context_loader_function:
        raise ValueError("LoadedPlugin context_loader_function must be defined when resource_data_type is present")
