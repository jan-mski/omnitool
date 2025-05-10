from pathlib import Path

import pytest

from omnitool.plugin.base import (Plugin, PLUGIN_CONFIGURATION_FILE_NAME, PluginLocation)
from omnitool_plugin_base.plugin.base import PluginDefinition
from omnitool.plugin.configuration import PluginConfiguration


@pytest.fixture
def plugin_configuration_mock(mocker):
    """
    Creates a mock PluginConfiguration for testing.
    
    Returns:
        MagicMock: A mocked PluginConfiguration instance
    """
    return mocker.MagicMock(spec=PluginConfiguration)


@pytest.fixture
def plugin_definition(context_resource_type):
    """
    Creates a test PluginDefinition with a fixed name and resource data type.
    
    Returns:
        PluginDefinition: A plugin definition for testing
    """
    return PluginDefinition(name="test_plugin", resource_type=context_resource_type)


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
def plugin(plugin_configuration_mock, plugin_definition, plugin_location):
    """
    Creates a Plugin instance using the provided fixtures.
    
    Returns:
        Plugin: A plugin instance for testing
    """
    return Plugin(
        configuration=plugin_configuration_mock,
        definition=plugin_definition,
        location=plugin_location
    )


def test_plugin_name(plugin, plugin_definition):
    """
    Tests that the plugin's name property correctly returns the name from the plugin definition.
    Expects the plugin name to match the name in the plugin definition.
    """
    assert plugin.name == plugin_definition.name


def test_plugin_location_configuration_file(plugin_location):
    """
    Tests that the plugin_location's configuration_file property correctly returns the expected path.
    Expects the configuration_file to be the configuration directory joined with configuration file name.
    """
    expected_file = plugin_location.configuration_dir / PLUGIN_CONFIGURATION_FILE_NAME

    assert plugin_location.configuration_file == expected_file


def test_plugin_location_plugin_name(plugin_location):
    """
    Tests that the plugin_location's plugin_name property correctly returns the name of the plugin module.
    Expects the plugin_name to be the name of the plugin module.
    """
    expected_name = plugin_location.plugin_module.name

    assert plugin_location.plugin_name == expected_name
