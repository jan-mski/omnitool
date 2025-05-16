import logging

from omnitool_plugin_base.plugin.base import PluginDefinition

from omnitool.plugin import finder
from omnitool.plugin.base import Plugin
from omnitool.plugin.finder import PluginLocation
from omnitool.plugin.configuration import load_configuration, PluginConfiguration


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
        logger.debug("No plugins available to load")
        return

    logger.debug("Loading plugins...")

    for plugin_location in plugin_locations:
        try:
            loaded_plugin: Plugin = _load_plugin(plugin_location)

            if loaded_plugin:
                loaded_plugins[loaded_plugin.name] = loaded_plugin
                logger.debug(f"Plugin '{loaded_plugin.name}' loaded from '{plugin_location.plugin_module.source}'")
        except Exception as e:
            logger.debug(f"Failed to load plugin '{plugin_location.plugin_name}' "
                         f"from {plugin_location.plugin_module.source}", e)

    logger.debug(f"Plugins loaded: {list(loaded_plugins.keys())}")


def _load_plugin(plugin_location: PluginLocation) -> Plugin:
    plugin_definition: PluginDefinition = plugin_location.load_module()
    _validate_plugin_definition(plugin_definition)

    plugin_configuration: PluginConfiguration = load_configuration(plugin_location.plugin_name)

    return Plugin(plugin_configuration, plugin_definition, plugin_location)


def _validate_plugin_definition(plugin_definition: PluginDefinition) -> None:
    if not isinstance(plugin_definition, PluginDefinition):
        raise ValueError("Plugin definition must be of type PluginDefinition")
    if plugin_definition.resource_operations and not plugin_definition.resource_type:
        raise ValueError("Plugin resource_type must be defined when resource operations are present")
