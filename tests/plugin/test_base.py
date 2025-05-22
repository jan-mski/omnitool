import pytest

from omnitool.plugin.base import (Plugin, PluginLocation)
from omnitool_plugin_base.plugin.base import PluginDefinition
from omnitool.plugin.configuration import PluginConfiguration
from omnitool.plugin.data import PluginData


@pytest.fixture
def plugin_configuration_mock(mocker):
    """
    Creates a mock PluginConfiguration for testing.

    Returns:
        MagicMock: A mocked PluginConfiguration instance
    """
    return mocker.MagicMock(spec=PluginConfiguration)


@pytest.fixture
def plugin_data_mock(mocker):
    """
    Creates a mock PluginData for testing.

    Returns:
        MagicMock: A mocked PluginData instance
    """
    return mocker.MagicMock(spec=PluginData)


@pytest.fixture
def plugin_definition(context_resource_type):
    """
    Creates a test PluginDefinition with a fixed name and resource data type.

    Returns:
        PluginDefinition: A plugin definition for testing
    """
    return PluginDefinition(root_operation_name="test_plugin", resource_type=context_resource_type)


@pytest.fixture
def plugin_location(mocker):
    """
    Creates a test PluginLocation with a mock plugin module.

    Returns:
        PluginLocation: A plugin location for testing
    """
    mock_module = mocker.MagicMock()
    return PluginLocation(plugin_module=mock_module)


@pytest.fixture
def plugin(plugin_configuration_mock, plugin_data_mock, plugin_definition, plugin_location):
    """
    Creates a Plugin instance using the provided fixtures.

    Returns:
        Plugin: A plugin instance for testing
    """
    return Plugin(
        data=plugin_data_mock,
        configuration=plugin_configuration_mock,
        definition=plugin_definition,
        location=plugin_location
    )


def test_plugin(plugin, plugin_location, plugin_configuration_mock, plugin_data_mock, plugin_definition):
    """
    Tests that the plugin's name property correctly returns the name from the plugin definition.
    Expects the plugin name to match the name in the plugin definition.
    """
    assert plugin.name == plugin_location.plugin_name
    assert plugin.data == plugin_data_mock
    assert plugin.configuration == plugin_configuration_mock
    assert plugin.definition == plugin_definition
    assert plugin.location == plugin_location


def test_plugin_location_plugin_name(plugin_location):
    """
    Tests that the plugin_location's plugin_name property correctly returns the name of the plugin module.
    Expects the plugin_name to be the name of the plugin module.
    """
    expected_name = plugin_location.plugin_module.name

    assert plugin_location.plugin_name == expected_name
