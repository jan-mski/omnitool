import logging

from omnitool.plugin.configuration import PluginConfiguration
from omnitool_plugin_base.plugin.base import PluginDefinition

logger = logging.getLogger(__name__)


def load_data(plugin_name: str, plugin_configuration: PluginConfiguration, plugin_definition: PluginDefinition):
    logger.debug(f"Loading data for plugin '{plugin_name}'")

    # TODO: also, the return value should be returned to the caller and set on the Plugin instance
    for context_name, context_resources in plugin_configuration.contexts.items():
        logger.debug(f"Loading data for context '{context_name}'")
        plugin_definition.resource_loader_function(configurations=context_resources)

    logger.debug("Data loaded successfully")
