import json

import pytest

from omnitool.plugin.loading.configuration import PluginConfiguration
from omnitool.plugin.api.context import ResourceData, Context
from omnitool.plugin.api.definition import PluginDefinition


@pytest.fixture
def resource_data_type():
    """
    Provides a ResourceData type for testing purposes.
    """
    class ResourceDataStub(ResourceData):
        pass

    return ResourceDataStub


@pytest.fixture
def configuration_json():
    """
    Provides a test configuration in JSON format with sample contexts and resources.

    Returns:
        str: A JSON string representing plugin configuration with contexts and resources
    """
    return json.dumps({
        "contexts": [
            {
                "name": "Context 1",
                "resources": [
                    {
                        "name": "Resource 1",
                        "uri": "file:///path/to/resource1"
                    },
                    {
                        "name": "Resource 2",
                        "uri": "file:///path/to/resource2"
                    }
                ]
            },
            {
                "name": "Context 2",
                "resources": {}
            }
        ]
    })


@pytest.fixture
def create_configuration_model():
    """
    Creates a factory function that returns validated PluginConfiguration model with test data.

    Returns:
        callable: A factory function that creates PluginConfiguration instances with populated resource data
    """
    def _create_configuration_model():
        return PluginConfiguration(contexts=[
            {
                "name": "Context 1",
                "resources": [
                    {
                        "name": "Resource 1",
                        "uri": "file:///path/to/resource1"
                    },
                    {
                        "name": "Resource 2",
                        "uri": "file:///path/to/resource2"
                    }
                ]
            },
            {
                "name": "Context 2",
                "resources": {}
            }
        ])
    
    return _create_configuration_model


@pytest.fixture
def resource_data(resource_data_type) -> ResourceData:
    """
    Provides a ResourceData instance for testing purposes.
    """
    return resource_data_type()


@pytest.fixture
def context_loader_function(resource_data) -> callable:
    """
    Provides a mock context loader function that initializes resources with the given resource data type.
    """
    def _context_loader_function(context: Context) -> None:
        """
        Mock context loader function that initializes resources with the specified resource data type.
        """
        for resource in context.resources.values():
            resource.data = resource_data

    return _context_loader_function


@pytest.fixture
def create_plugin_definition(resource_data_type, context_loader_function) -> callable:
    """
    Creates a factory function that returns a PluginDefinition object with the given resource data type and context loader function.

    Returns:
        callable: A factory function that creates PluginDefinition instances with the given resource data type and context loader function.
    """
    def _create_plugin_definition(plugin_name: str) -> PluginDefinition:
        """
        Creates a PluginDefinition object for testing.

        Args:
            plugin_name: The name of the plugin.

        Returns:
            PluginDefinition: A PluginDefinition object with resource type and loader defined.
        """
        plugin_definition = PluginDefinition(root_operation_name=plugin_name, resource_data_type=resource_data_type)
        plugin_definition.context_loader_function = context_loader_function
        return plugin_definition

    return _create_plugin_definition
