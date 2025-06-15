import logging
from dataclasses import dataclass

from omnitool.plugin.loading.configuration import PluginConfiguration
from omnitool.plugin.loading.configuration import ContextConfiguration, ResourceConfiguration
from omnitool.plugin.api.context import ResourceData, Context, Resource, parse_uri
from omnitool.plugin.api.definition import PluginDefinition, ContextLoaderProtocol


logger = logging.getLogger(__name__)


@dataclass
class PluginData:
    """
    Data class containing all the data for a plugin.

    Attributes:
        contexts: A dictionary of contexts, where the key is the name of the context and the value is the context.
    """
    contexts: dict[str, Context]


class PluginDataLoadError(Exception):
    def __init__(self, additional_info: str):
        super().__init__(f"Could not load plugin data: {additional_info}")


def load_data(plugin_name: str,
              plugin_configuration: PluginConfiguration,
              plugin_definition: PluginDefinition) -> PluginData:
    """
    Loads the data for the plugin.

    Args:
        plugin_name: The name of the plugin.
        plugin_configuration: The configuration of the plugin.
        plugin_definition: The definition of the plugin.

    Returns:
        A PluginData object containing the contexts for the plugin.
    """
    logger.debug(f"Loading data for plugin '{plugin_name}'")

    contexts = {}

    try:
        for context_name, context_configuration in plugin_configuration.contexts.items():
            logger.debug(f"Loading data for context '{context_name}'")
            context: Context = _load_context(plugin_definition.context_loader_function, context_configuration)
            contexts[context_name] = context
    except Exception as e:
        raise PluginDataLoadError(str(e)) from e

    logger.debug(f"Data loaded successfully for plugin '{plugin_name}")

    return PluginData(contexts=contexts)


def _load_context(context_loader_function: ContextLoaderProtocol,
                  context_configuration: ContextConfiguration) -> Context:
    context = Context(name=context_configuration.name,
                      resources=_map_resource_configurations_to_resources(context_configuration.resources))
    context_loader_function(context=context)

    return context


def _map_resource_configurations_to_resources(resources: dict[str, ResourceConfiguration]) -> dict[str, Resource]:
    return {name: Resource(name=name, location=parse_uri(resource_configuration.uri))
            for name, resource_configuration in resources.items()}
