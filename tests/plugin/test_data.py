import pytest
from omnitool.plugin.configuration import PluginConfiguration
from omnitool.plugin.data import PluginDataLoadError, load_data
from omnitool_plugin_base.plugin.base import PluginDefinition, ContextResource
from omnitool.plugin.base import Context


def test_load_data_loads_resources(mocker, configuration_model):
    """
    Tests that load_data correctly loads resources for each context and returns the expected mapping.
    Expects the resource loader function to be called for each context and the loaded resources to be returned.
    """
    expected_contexts = {
        context_name: Context(
            resources={
                resource_name: mocker.Mock(spec=ContextResource)
                for resource_name in context_configuration.resources.keys()            },
            configuration=context_configuration
        )
        for context_name, context_configuration in configuration_model.contexts.items()
    }
    expected_calls = [
        mocker.call(configurations=list(context_configuration.resources.values()))
        for context_configuration in configuration_model.contexts.values()
    ]

    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)
    mock_plugin_definition.resource_loader_function.side_effect = [
        list(context.resources.values())
        for context in expected_contexts.values()
    ]

    actual_contexts = load_data("test_plugin", configuration_model, mock_plugin_definition)

    assert actual_contexts == expected_contexts
    assert mock_plugin_definition.resource_loader_function.call_count == len(configuration_model.contexts)
    mock_plugin_definition.resource_loader_function.assert_has_calls(expected_calls)


def test_load_data_handles_empty_contexts(mocker):
    """
    Tests load_data behavior when the plugin configuration has no contexts.
    Expects the resource loader function not to be called and an empty dict to be returned.
    """
    configuration_model = PluginConfiguration()
    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)

    result = load_data("test_plugin", configuration_model, mock_plugin_definition)

    assert result == {}
    mock_plugin_definition.resource_loader_function.assert_not_called()


def test_load_data_handles_exceptions(mocker, configuration_model):
    """
    Tests that load_data handles exceptions raised by the resource loader function.
    Expects an exception to be raised.
    """
    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)
    mock_plugin_definition.resource_loader_function.side_effect = Exception("Test exception")

    with pytest.raises(PluginDataLoadError):
        load_data("test_plugin", configuration_model, mock_plugin_definition)
