from pathlib import Path
from urllib.parse import urlparse
import pytest

from omnitool.plugin.loading.configuration import PluginConfiguration
from omnitool.plugin.loading.data import PluginDataLoadError, load_data, PluginData
from omnitool.plugin.api.context import ResourceData, Context, Resource, Location
from omnitool.plugin.api.definition import PluginDefinition


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
def plugin_definition(resource_data_type, context_loader_function) -> PluginDefinition:
    """
    Provides a mock PluginDefinition for testing purposes.
    """
    plugin_definition = PluginDefinition(root_operation_name="test_plugin", resource_data_type=resource_data_type)
    plugin_definition.context_loader_function = context_loader_function

    return plugin_definition


@pytest.fixture
def invalid_uri_configuration():
    """
    Provides a PluginConfiguration with invalid URI for testing error handling.
    """
    return PluginConfiguration(contexts=[
        {
            "name": "test_context",
            "resources": [
                {
                    "name": "test_resource",
                    "uri": "http://invalid-scheme/resource"
                }
            ]
        }
    ])


def test_load_data_loads_resources(resource_data, configuration_model, plugin_definition):
    """
    Tests that load_data correctly loads resources for each context and returns the expected mapping.
    Expects the context loader function to be called for each context and the loaded resources to be returned.
    """
    expected_contexts = {
        context_name: Context(
            name=context_name,
            resources={
                resource_name: Resource(
                    name=resource_name,
                    location=Location(path=Path(urlparse(resource_configuration.uri).path)),
                    data=resource_data
                )
                for resource_name, resource_configuration in context_configuration.resources.items()
            }
        )
        for context_name, context_configuration in configuration_model.contexts.items()
    }
    expected_data = PluginData(contexts=expected_contexts)

    actual_data = load_data("test_plugin", configuration_model, plugin_definition)

    assert actual_data == expected_data


def test_load_data_handles_empty_contexts(mocker):
    """
    Tests load_data behavior when the plugin configuration has no contexts.
    Expects the context loader function not to be called and an empty dict to be returned.
    """
    configuration_model = PluginConfiguration()
    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)

    result = load_data("test_plugin", configuration_model, mock_plugin_definition)

    assert result == PluginData(contexts={})
    mock_plugin_definition.context_loader_function.assert_not_called()


def test_load_data_handles_exceptions(mocker, configuration_model):
    """
    Tests that load_data handles exceptions raised by the context loader function.
    Expects an exception to be raised.
    """
    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)
    mock_plugin_definition.context_loader_function.side_effect = Exception("Test exception")

    with pytest.raises(PluginDataLoadError):
        load_data("test_plugin", configuration_model, mock_plugin_definition)


def test_load_data_handles_invalid_uri(invalid_uri_configuration, plugin_definition):
    """
    Tests that load_data handles invalid URIs in resource configurations.
    Expects a PluginDataLoadError to be raised when create_location fails due to invalid URI.
    """
    with pytest.raises(PluginDataLoadError, match="Could not load plugin data"):
        load_data("test_plugin", invalid_uri_configuration, plugin_definition)
