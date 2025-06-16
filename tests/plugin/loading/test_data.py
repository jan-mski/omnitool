from pathlib import Path
from urllib.parse import urlparse
import pytest

from omnitool.plugin.loading.configuration import PluginConfiguration
from omnitool.plugin.loading.data import PluginDataLoadError, load_data, PluginData
from omnitool.plugin.api.context import Context, Resource, Location
from omnitool.plugin.api.definition import PluginDefinition


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


def test_load_data_loads_resources(resource_data, create_configuration_model, create_plugin_definition):
    """
    Tests that load_data correctly loads resources for each context and returns the expected mapping.
    Expects the context loader function to be called for each context and the loaded resources to be returned.
    """
    plugin_name = "test_plugin"
    plugin_definition = create_plugin_definition(plugin_name)
    configuration_model = create_configuration_model()

    expected_data = PluginData(contexts={
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
    })

    actual_data = load_data(plugin_name, configuration_model, plugin_definition)

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


def test_load_data_handles_exceptions(mocker, create_configuration_model):
    """
    Tests that load_data handles exceptions raised by the context loader function.
    Expects an exception to be raised.
    """
    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)
    mock_plugin_definition.context_loader_function.side_effect = Exception("Test exception")
    configuration_model = create_configuration_model()

    with pytest.raises(PluginDataLoadError):
        load_data("test_plugin", configuration_model, mock_plugin_definition)


def test_load_data_handles_invalid_uri(invalid_uri_configuration, create_plugin_definition):
    """
    Tests that load_data handles invalid URIs in resource configurations.
    Expects a PluginDataLoadError to be raised when create_location fails due to invalid URI.
    """
    plugin_name = "test_plugin"
    plugin_definition = create_plugin_definition(plugin_name)

    with pytest.raises(PluginDataLoadError, match="Could not load plugin data"):
        load_data(plugin_name, invalid_uri_configuration, plugin_definition)
