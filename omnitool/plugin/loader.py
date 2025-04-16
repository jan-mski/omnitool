import logging

from omnitool_plugin_base.plugin.base import PluginDefinition

from omnitool.plugin import finder, configuration
from omnitool.plugin.base import Plugin
from omnitool.plugin.finder import PluginLocation
from omnitool.plugin.configuration import PluginConfigurationService


logger = logging.getLogger(__name__)
loaded_plugins: dict[str, Plugin] = {}


def load_plugins() -> None:
    """
    Finds and loads all available plugins.
    """
    global loaded_plugins
    loaded_plugins = {}

    plugin_locations: list[PluginLocation] = finder.find_plugins()

    if not plugin_locations:
        logger.warning("No plugins available to load")
        return

    for location in plugin_locations:
        try:
            loaded_plugin: Plugin = _load_plugin(location)

            if loaded_plugin:
                loaded_plugins[loaded_plugin.name] = loaded_plugin
                logger.info(f"Plugin '{loaded_plugin.name}' loaded from '{location.plugin_module.source}'")
        except Exception as e:
            logger.warning(f"Failed to load plugin {location.plugin_name}' "
                           f"from {location.plugin_module.source}: {str(e)}")
            logger.debug(e)


def _load_plugin(location: PluginLocation) -> Plugin:
    plugin_definition: PluginDefinition = location.load_module()
    _validate_plugin_definition(plugin_definition)

    configuration_service: PluginConfigurationService = configuration.plugin_configuration_service(
        configuration_file=location.configuration_file,
        resource_data_type=plugin_definition.resource_data_type)

    return Plugin(configuration_service, plugin_definition, location)


def _validate_plugin_definition(plugin_definition: PluginDefinition) -> None:
    if not isinstance(plugin_definition, PluginDefinition):
        raise ValueError("Plugin definition must be of type PluginDefinition")
