import json
from typing import Optional

import pytest

from omnitool.plugin.loading.configuration import PluginConfiguration
from omnitool.plugin.api.context import Context
from omnitool.plugin.api.definition import PluginDefinition
from omnitool.plugin.loading.location import PluginModule
from omnitool.plugin.loading.loader import LoadedPlugin
from omnitool.plugin.loading.data import PluginData


@pytest.fixture
def resource_data_type():
    """
    Provides a resource data type for testing purposes.
    """

    class ResourceDataStub:
        pass

    return ResourceDataStub


@pytest.fixture
def configuration_json():
    """
    Provides a test configuration in JSON format with sample contexts and resources.

    Returns:
        str: A JSON string representing plugin configuration with contexts and resources
    """
    return json.dumps(
        {
            "contexts": [
                {
                    "name": "Context 1",
                    "resources": [
                        {"name": "Resource 1", "uri": "file:///path/to/resource1"},
                        {"name": "Resource 2", "uri": "file:///path/to/resource2"},
                    ],
                },
                {"name": "Context 2", "resources": []},
            ]
        }
    )


@pytest.fixture
def create_configuration_model():
    """
    Creates a factory function that returns validated PluginConfiguration model with test data.

    Returns:
        callable: A factory function that creates PluginConfiguration instances with populated resource data
    """

    def _create_configuration_model():
        return PluginConfiguration(
            contexts=[
                {
                    "name": "Context 1",
                    "resources": [
                        {"name": "Resource 1", "uri": "file:///path/to/resource1"},
                        {"name": "Resource 2", "uri": "file:///path/to/resource2"},
                    ],
                },
                {"name": "Context 2", "resources": []},
            ]
        )

    return _create_configuration_model


@pytest.fixture
def resource_data(resource_data_type):
    """
    Provides a resource data instance for testing purposes.
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


@pytest.fixture
def mock_plugin_module(mocker) -> callable:
    def _mock_plugin_module(plugin_name: str, plugin_definition: PluginDefinition) -> mocker.MagicMock:
        """
        Creates a mock PluginModule object for testing.

        Args:
            plugin_name: The name of the plugin.
            plugin_definition: The plugin definition object.

        Returns:
            MagicMock: A mocked PluginModule object.
        """
        module_mock = mocker.MagicMock(spec=PluginModule)
        module_mock.source = "plugin_source"
        module_mock.root_operation_name = plugin_name
        module_mock.name = plugin_name
        module_mock.load.return_value = plugin_definition

        return module_mock

    return _mock_plugin_module


@pytest.fixture
def mock_plugin_operations():
    """
    Factory fixture for creating mock plugin operations.
    """

    def _mock_plugin_operations(operation_names: list[str]) -> list:
        """
        Creates mock operations for the given operation names.

        Args:
            operation_names: List of operation names to create mock operations for.

        Returns:
            list: List of mock operation functions.
        """
        operations = []
        for operation_name in operation_names:

            def operation_stub(context: Context):
                pass

            operation_stub.__name__ = operation_name
            operations.append(operation_stub)

        return operations

    return _mock_plugin_operations


@pytest.fixture
def create_loaded_plugin(mock_plugin_module, create_plugin_definition, mock_plugin_operations) -> callable:
    def _create_loaded_plugin(
        plugin_name: str,
        plugin_definition: Optional[PluginDefinition] = None,
        operation_names: Optional[list[str]] = None,
        contexts: Optional[dict] = None,
    ) -> LoadedPlugin:
        """
        Creates a LoadedPlugin object with mocked components for testing.

        Args:
            plugin_name: The name of the plugin.
            plugin_definition: Optional PluginDefinition object. If not provided, one will be created.
            operation_names: Optional list of operation names to create mock operations for.
            contexts: Optional dict of contexts to add to the plugin data. If not provided, no contexts will be set.

        Returns:
            LoadedPlugin: A LoadedPlugin object with mocked module and contexts.
        """
        if plugin_definition is None:
            plugin_definition = create_plugin_definition(plugin_name)

        if operation_names is not None:
            operations = mock_plugin_operations(operation_names)
            plugin_definition.operations.extend(operations)

        module_mock = mock_plugin_module(plugin_name=plugin_name, plugin_definition=plugin_definition)

        plugin_data = PluginData(contexts or {})

        return LoadedPlugin(data=plugin_data, definition=plugin_definition, module=module_mock)

    return _create_loaded_plugin
