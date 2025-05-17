from omnitool.plugin.configuration import PluginConfiguration
from omnitool.plugin.data import load_data
from omnitool_plugin_base.plugin.base import PluginDefinition


def test_load_data_calls_resource_loader(mocker, configuration_model):
    """
    Tests that load_data correctly passes the plugin configuration contexts to the plugin's resource loader function.
    Expects the resource loader function to be called for each context with its resources.
    """
    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)
    
    load_data("test_plugin", configuration_model, mock_plugin_definition)

    assert mock_plugin_definition.resource_loader_function.call_count == len(configuration_model.contexts)
    
    expected_calls = [
        mocker.call(configurations=context_resources) 
        for context_resources in configuration_model.contexts.values()
    ]
    mock_plugin_definition.resource_loader_function.assert_has_calls(expected_calls)


def test_load_data_handles_empty_contexts(mocker):
    """
    Tests load_data behavior when the plugin configuration has no contexts.
    Expects the resource loader function not to be called.
    """
    configuration_model = PluginConfiguration()
    mock_plugin_definition = mocker.Mock(spec=PluginDefinition)

    load_data("test_plugin", configuration_model, mock_plugin_definition)

    mock_plugin_definition.resource_loader_function.assert_not_called()
