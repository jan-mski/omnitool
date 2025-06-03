import logging
from dataclasses import dataclass

from omnitool.plugin.configuration import PluginConfiguration
from omnitool_plugin_base.plugin.base import PluginDefinition, ContextResource, ResourceLoaderProtocol
from omnitool_plugin_base.plugin.configuration import ResourceConfiguration


logger = logging.getLogger(__name__)


@dataclass
class Context:
    """
    Data class containing all the data for a context.

    Attributes:
        resources: A dictionary of resources, where the key is the name of the resource and the value is the resource.
    """
    resources: dict[str, ContextResource]


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
            resource_configurations = list(context_configuration.resources.values())
            resources: dict[str, ContextResource] = _load_resources(plugin_definition.resource_loader_function,
                                                                    resource_configurations)
            contexts[context_name] = Context(resources=resources)
    except Exception as e:
        raise PluginDataLoadError(str(e)) from e

    logger.debug(f"Data loaded successfully for plugin '{plugin_name}")

    return PluginData(contexts=contexts)


def _load_resources(resource_loader_function: ResourceLoaderProtocol,
                    resource_configurations: list[ResourceConfiguration]) -> dict[str, ContextResource]:
    resources: list[ContextResource] = resource_loader_function(resource_configurations=resource_configurations)
    return {resource_configuration.name: resource
            for resource_configuration, resource in zip(resource_configurations, resources)}
