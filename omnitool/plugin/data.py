import logging
from dataclasses import dataclass

from omnitool.plugin.configuration import PluginConfiguration
from omnitool.plugin.configuration import ContextConfiguration, ResourceConfiguration
from omnitool.plugin.context import ResourceData, Context, Resource
from omnitool.plugin.definition import PluginDefinition, ContextLoaderProtocol


logger = logging.getLogger(__name__)


@dataclass
class ContextData:
    """
    Data class containing all the data for a context.

    Attributes:
        resources: A dictionary of resources, where the key is the name of the resource and the value is the resource.
    """
    resources: dict[str, ResourceData]


@dataclass
class PluginData:
    """
    Data class containing all the data for a plugin.

    Attributes:
        contexts: A dictionary of contexts, where the key is the name of the context and the value is the context.
    """
    contexts: dict[str, ContextData]


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
            contexts[context_name] = ContextData(resources=_map_resources_to_resource_data(context.resources))
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


def _map_resources_to_resource_data(resources: dict[str, Resource]) -> dict[str, ResourceData]:
    return {name: resource.data for name, resource in resources.items()}


def _map_resource_configurations_to_resources(resources: dict[str, ResourceConfiguration]) -> dict[str, Resource]:
    return {name: Resource(name=name, location=resource_configuration.location)
            for name, resource_configuration in resources.items()}
