import pytest
import omnitool.plugin.loader as loader
import omnitool.plugin.finder
import omnitool.plugin.configuration

from pathlib import Path
from omnitool_plugin_base.plugin.base import PluginDefinition
from omnitool.plugin.base import Plugin, PluginLocation
from omnitool.plugin.configuration import PluginConfigurationService
from tests.plugin.utils import ContextResourceDataStub


@pytest.fixture
def mock_plugin_location(mocker) -> callable:
    def _mock_plugin_location(plugin_name: str,
                              source: str,
                              configuration_dir: str,
                              plugin_def: PluginDefinition) -> mocker.MagicMock:
        """
        Creates a mock PluginLocation object for testing.

        Args:
            plugin_name: The name of the plugin.
            source: The source path of the plugin.
            configuration_dir: The configuration directory of the plugin.
            plugin_def: The plugin definition object.

        Returns:
            MagicMock: A mocked PluginLocation object.
        """
        module_mock = mocker.MagicMock()
        module_mock.source = source
        module_mock.name = plugin_name

        location_mock = mocker.MagicMock()
        location_mock.plugin_name = plugin_name
        location_mock.plugin_module = module_mock
        location_mock.configuration_dir = Path(configuration_dir)
        location_mock.load_module.return_value = plugin_def

        return location_mock

    return _mock_plugin_location


@pytest.fixture
def logger_mock(mocker):
    """
    Creates a mock for the loader's logger.
    
    Returns:
        MagicMock: A mocked logger object.
    """
    return mocker.patch("omnitool.plugin.loader.logger")


@pytest.fixture
def mock_find_plugins(mocker):
    def _mock_find_plugins(plugin_locations: list[PluginLocation] = None):
        """
        Sets up the find_plugins mock to return the specified plugin locations.
        
        Args:
            plugin_locations: List of plugin location mocks to be returned by find_plugins.
                              Defaults to an empty list if None is provided.
        
        Returns:
            MagicMock: The patched find_plugins mock object.
        """
        if plugin_locations is None:
            plugin_locations = []
            
        mock = mocker.patch.object(omnitool.plugin.finder, "find_plugins", return_value=plugin_locations)
        return mock
        
    return _mock_find_plugins


@pytest.fixture
def mock_configuration_service_factory(mocker):
    def _mock_configuration_service_factory(configuration_services: list[PluginConfigurationService]):
        """
        Sets up the plugin_configuration_service mock to return the specified 
        configuration services as side effects.
        
        Args:
            configuration_services: List of configuration service mocks to be
                                         returned as side effects.
        """
        configuration_service_mock = mocker.patch.object(omnitool.plugin.configuration, "plugin_configuration_service")
        configuration_service_mock.side_effect = configuration_services
        
    return _mock_configuration_service_factory


def test_load_plugins_no_plugins_found(mock_find_plugins, logger_mock):
    """
    Tests the behavior when no plugins are available to load.
    Expects the function to log a warning and return without loading anything.
    """
    mock_find_plugins()

    loader.load_plugins()

    logger_mock.warning.assert_called_once()

    assert loader.loaded_plugins == {}


def test_load_plugins_successful_loading(mocker,
                                         mock_plugin_location,
                                         mock_find_plugins,
                                         mock_configuration_service_factory,
                                         logger_mock):
    """
    Tests the loading of multiple available plugins.
    Expects all plugins to be loaded correctly and stored in the loaded_plugins dictionary.
    """
    plugin1_name = "plugin1"
    plugin2_name = "plugin2"
    plugin1_definition_mock = PluginDefinition(name=plugin1_name, resource_data_type=ContextResourceDataStub)
    plugin2_definition_mock = PluginDefinition(name=plugin2_name, resource_data_type=ContextResourceDataStub)

    plugin1_location_mock = mock_plugin_location(
        plugin_name=plugin1_name,
        source="/path/to/plugin1",
        configuration_dir="/path/to/config1",
        plugin_def=plugin1_definition_mock
    )
    plugin2_location_mock = mock_plugin_location(
        plugin_name=plugin2_name,
        source="/path/to/plugin2",
        configuration_dir="/path/to/config2",
        plugin_def=plugin2_definition_mock
    )
    mock_find_plugins([plugin1_location_mock, plugin2_location_mock])

    plugin1_configuration_service_mock = mocker.MagicMock()
    plugin2_configuration_service_mock = mocker.MagicMock()
    mock_configuration_service_factory([plugin1_configuration_service_mock, plugin2_configuration_service_mock])

    loader.load_plugins()

    expected_plugins = {
        plugin1_name: Plugin(
            configuration_service=plugin1_configuration_service_mock,
            definition=plugin1_definition_mock,
            location=plugin1_location_mock
        ),
        plugin2_name: Plugin(
            configuration_service=plugin2_configuration_service_mock,
            definition=plugin2_definition_mock,
            location=plugin2_location_mock
        )
    }

    assert loader.loaded_plugins == expected_plugins

    logger_mock.warning.assert_not_called()


def test_load_plugins_multiple_plugins_with_exceptions(mocker, mock_find_plugins, logger_mock):
    """
    Tests loading multiple plugins where some succeed and some fail.
    Expects successful plugins to be loaded and exceptions to be handled properly
    without affecting other plugins.
    """
    pass


def test_load_plugins_all_plugins_fail(mocker, mock_find_plugins, logger_mock):
    """
    Tests the scenario where all plugins fail to load.
    Expects appropriate error logging for each plugin and an empty loaded_plugins dictionary.
    """
    pass


def test_load_plugins_resets_loaded_plugins(mocker, mock_find_plugins, logger_mock):
    """
    Tests that the global loaded_plugins dictionary is reset when the function is called.
    Expects any previously loaded plugins to be removed before loading new ones.
    """
    pass

