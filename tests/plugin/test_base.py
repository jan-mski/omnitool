from pathlib import Path

import pytest
from omnitool.plugin.base import (Plugin, PluginConfigurationService, ContextConfiguration,
                                  ContextResourceConfiguration, PLUGIN_CONFIGURATION_FILE_NAME)
from omnitool.plugin.base import PluginLocation
from omnitool_plugin_base.plugin.data import ContextResourceLocation
from omnitool_plugin_base.plugin.base import PluginDefinition
from tests.plugin.utils import ContextResourceDataStub


@pytest.fixture
def plugin_config_service_mock(mocker):
    """
    Creates a mock PluginConfigurationService for testing.
    
    Returns:
        Mock: A mocked PluginConfigurationService instance
    """
    return mocker.MagicMock(spec=PluginConfigurationService)


@pytest.fixture
def plugin_definition():
    """
    Creates a test PluginDefinition with a fixed name and resource data type.
    
    Returns:
        PluginDefinition: A plugin definition for testing
    """
    return PluginDefinition(name="test_plugin", resource_data_type=ContextResourceDataStub)


@pytest.fixture
def plugin_location(mocker):
    """
    Creates a test PluginLocation with a predetermined configuration directory.
    
    Returns:
        PluginLocation: A plugin location for testing
    """
    return PluginLocation(configuration_dir=Path("/root/dir/"),
                          plugin_module=mocker.MagicMock())


@pytest.fixture
def plugin(plugin_config_service_mock, plugin_definition, plugin_location):
    """
    Creates a Plugin instance using the provided fixtures.
    
    Returns:
        Plugin: A plugin instance for testing
    """
    return Plugin(
        configuration_service=plugin_config_service_mock,
        definition=plugin_definition,
        location=plugin_location
    )


@pytest.fixture
def context_resource_configuration():
    """
    Creates a test ContextResourceConfiguration with a fixed name and location.
    
    Returns:
        ContextResourceConfiguration: A resource configuration for testing
    """
    return ContextResourceConfiguration(name="test_resource",
                                        location=ContextResourceLocation(path=Path("/root/dir/context/resource")))


@pytest.fixture
def context_configuration(context_resource_configuration):
    """
    Creates a test ContextConfiguration containing a test resource.
    
    Returns:
        ContextConfiguration: A context configuration for testing
    """
    return ContextConfiguration(name="test_context",
                                resources={context_resource_configuration.name: context_resource_configuration})


def test_plugin_name(plugin, plugin_definition):
    """
    Tests that the plugin's name property correctly returns the name from the plugin definition.
    
    Expects the plugin name to match the name in the plugin definition.
    """
    assert plugin.name == plugin_definition.name


def test_plugin_get_contexts(plugin, plugin_config_service_mock, context_configuration):
    """
    Tests that the plugin's get_contexts method correctly delegates to the configuration service.
    
    Expects the plugin to return the contexts from the configuration service.
    """
    expected_contexts = {context_configuration.name: context_configuration}
    plugin_config_service_mock.get_contexts.return_value = expected_contexts

    assert plugin.get_contexts() == expected_contexts


def test_plugin_add_resource(plugin, plugin_config_service_mock, context_resource_configuration):
    """
    Tests that the plugin's add_resource method correctly delegates to the configuration service.
    
    Expects the plugin to call the configuration service's add_resource with the correct arguments.
    """
    plugin.add_resource(context_id="test_context", resource=context_resource_configuration)

    plugin_config_service_mock.add_resource.assert_called_once_with("test_context", context_resource_configuration)


def test_plugin_location_configuration_file(plugin_location):
    """
    Tests that the plugin_location's configuration_file property correctly returns the expected path.
    
    Expects the configuration_file to be the configuration directory joined with configuration file name.
    """
    expected_file = plugin_location.configuration_dir / PLUGIN_CONFIGURATION_FILE_NAME

    assert plugin_location.configuration_file == expected_file
