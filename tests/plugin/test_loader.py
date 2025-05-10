import pytest
import omnitool.plugin.loader as loader
import omnitool.plugin.finder
import omnitool.plugin.configuration

from pathlib import Path
from omnitool_plugin_base.plugin.base import PluginDefinition
from omnitool.plugin.base import Plugin, PluginLocation
from omnitool.plugin.configuration import PluginConfiguration


@pytest.fixture
def mock_plugin_location(mocker, tmp_path) -> callable:
    def _mock_plugin_location(plugin_name: str, plugin_definition: PluginDefinition) -> mocker.MagicMock:
        """
        Creates a mock PluginLocation object for testing.

        Args:
            plugin_name: The name of the plugin.
            plugin_definition: The plugin definition object.

        Returns:
            MagicMock: A mocked PluginLocation object.
        """
        module_mock = mocker.MagicMock()
        module_mock.source = "plugin_source"
        module_mock.root_operation_name = plugin_name

        location_mock = mocker.MagicMock()
        location_mock.plugin_name = plugin_name
        location_mock.plugin_module = module_mock
        location_mock.configuration_dir = Path(tmp_path) / plugin_name
        location_mock.load_module.return_value = plugin_definition

        return location_mock

    return _mock_plugin_location


@pytest.fixture
def logger_mock(mocker):
    """
    Creates a mock for the loader's logger.

    Returns:
        MagicMock: A mocked logger object.
    """
    return mocker.patch.object(loader, "logger")


@pytest.fixture
def mock_find_plugins(mocker) -> callable:
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

        mocker.patch.object(omnitool.plugin.finder, "find_plugins", return_value=plugin_locations)

    return _mock_find_plugins


@pytest.fixture
def mock_load_configuration(mocker):
    def _mock_load_configuration(configurations: list[PluginConfiguration]):
        """
        Sets up the load_configuration mock to return the specified 
        configurations.

        Args:
            configurations: List of configuration mocks to be returned.
        """
        load_configuration_mock = mocker.patch.object(omnitool.plugin.loader, "load_configuration")
        load_configuration_mock.side_effect = configurations

    return _mock_load_configuration


def test_load_plugins_no_plugins_found(mock_find_plugins):
    """
    Tests the behavior when no plugins are available to load.
    Expects the function to log a warning and return without loading anything.
    """
    mock_find_plugins([])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_successful_loading(mocker,
                                         mock_plugin_location,
                                         mock_find_plugins,
                                         mock_load_configuration,
                                         context_resource_type):
    """
    Tests the loading of multiple available plugins.
    Expects all plugins to be loaded correctly and stored in the loaded_plugins dictionary.
    """
    plugin1_name = "plugin1"
    plugin2_name = "plugin2"
    plugin1_definition = PluginDefinition(root_operation_name=plugin1_name, resource_type=context_resource_type)
    plugin2_definition = PluginDefinition(root_operation_name=plugin2_name, resource_type=context_resource_type)

    plugin1_location_mock = mock_plugin_location(
        plugin_name=plugin1_name,
        plugin_definition=plugin1_definition
    )
    plugin2_location_mock = mock_plugin_location(
        plugin_name=plugin2_name,
        plugin_definition=plugin2_definition
    )
    mock_find_plugins([plugin1_location_mock, plugin2_location_mock])

    plugin1_configuration_mock = mocker.MagicMock()
    plugin2_configuration_mock = mocker.MagicMock()
    mock_load_configuration([plugin1_configuration_mock, plugin2_configuration_mock])

    loader.load_plugins()

    expected_plugins = {
        plugin1_name: Plugin(
            configuration=plugin1_configuration_mock,
            definition=plugin1_definition,
            location=plugin1_location_mock
        ),
        plugin2_name: Plugin(
            configuration=plugin2_configuration_mock,
            definition=plugin2_definition,
            location=plugin2_location_mock
        )
    }

    assert loader.loaded_plugins == expected_plugins


def test_load_plugins_multiple_plugins_with_exceptions(mocker,
                                                       mock_plugin_location,
                                                       mock_find_plugins,
                                                       mock_load_configuration,
                                                       context_resource_type):
    """
    Tests loading multiple plugins where some succeed and some fail.
    Expects successful plugins to be loaded and exceptions to be handled properly
    without affecting other plugins.
    """
    good_plugin_name = "good_plugin"
    good_plugin_definition = PluginDefinition(root_operation_name=good_plugin_name, resource_type=context_resource_type)
    good_plugin_location_mock = mock_plugin_location(
        plugin_name=good_plugin_name,
        plugin_definition=good_plugin_definition
    )
    
    bad_plugin1_name = "bad_plugin1"
    bad_plugin1_location_mock = mock_plugin_location(
        plugin_name=bad_plugin1_name,
        plugin_definition=None
    )
    
    bad_plugin2_name = "bad_plugin2"
    bad_plugin2_definition = PluginDefinition(root_operation_name=bad_plugin2_name, resource_type=context_resource_type)
    bad_plugin2_location_mock = mock_plugin_location(
        plugin_name=bad_plugin2_name,
        plugin_definition=bad_plugin2_definition
    )

    mock_find_plugins([good_plugin_location_mock, bad_plugin1_location_mock, bad_plugin2_location_mock])

    good_plugin_configuration_mock = mocker.MagicMock()
    mock_load_configuration([
        good_plugin_configuration_mock,
        Exception("Failed to load configuration")
    ])

    loader.load_plugins()

    expected_plugins = {
        good_plugin_name: Plugin(
            configuration=good_plugin_configuration_mock,
            definition=good_plugin_definition,
            location=good_plugin_location_mock
        )
    }

    assert loader.loaded_plugins == expected_plugins


def test_load_plugins_all_plugins_fail(mock_plugin_location, mock_find_plugins, context_resource_type):
    """
    Tests the scenario where all plugins fail to load.
    Expects appropriate warning log for each plugin and an empty loaded_plugins dictionary.
    """
    bad_plugin1_name = "bad_plugin1"
    bad_plugin1_definition = PluginDefinition(root_operation_name=bad_plugin1_name, resource_type=context_resource_type)
    bad_plugin1_location_mock = mock_plugin_location(
        plugin_name=bad_plugin1_name,
        plugin_definition=bad_plugin1_definition
    )
    bad_plugin1_location_mock.load_module.side_effect = ValueError("Invalid plugin definition")
    
    bad_plugin2_name = "bad_plugin2"
    bad_plugin2_definition = PluginDefinition(root_operation_name=bad_plugin2_name, resource_type=context_resource_type)
    bad_plugin2_location_mock = mock_plugin_location(
        plugin_name=bad_plugin2_name,
        plugin_definition=bad_plugin2_definition
    )
    bad_plugin2_location_mock.load_module.side_effect = ImportError("Could not import plugin module")

    mock_find_plugins([bad_plugin1_location_mock, bad_plugin2_location_mock])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_resets_loaded_plugins(mocker,
                                            mock_plugin_location,
                                            mock_find_plugins,
                                            mock_load_configuration,
                                            context_resource_type):
    """
    Tests that the global loaded_plugins dictionary is reset when the function is called.
    Expects any previously loaded plugins to be removed before loading new ones.
    """
    plugin1_name = "plugin1"
    plugin1_definition = PluginDefinition(root_operation_name=plugin1_name, resource_type=context_resource_type)
    plugin1_location_mock = mock_plugin_location(
        plugin_name=plugin1_name,
        plugin_definition=plugin1_definition
    )
    
    plugin2_name = "plugin2"
    plugin2_definition = PluginDefinition(root_operation_name=plugin2_name, resource_type=context_resource_type)
    plugin2_location_mock = mock_plugin_location(
        plugin_name=plugin2_name,
        plugin_definition=plugin2_definition
    )

    plugin1_configuration_mock = mocker.MagicMock()
    mock_load_configuration([plugin1_configuration_mock])
    mock_find_plugins([plugin1_location_mock])

    loader.load_plugins()

    expected_plugins = {
        plugin1_name: Plugin(
            configuration=plugin1_configuration_mock,
            definition=plugin1_definition,
            location=plugin1_location_mock
        )
    }

    assert loader.loaded_plugins == expected_plugins

    plugin2_configuration_mock = mocker.MagicMock()
    mock_load_configuration([plugin2_configuration_mock])
    mock_find_plugins([plugin2_location_mock])

    loader.load_plugins()

    expected_plugins = {
        plugin2_name: Plugin(
            configuration=plugin2_configuration_mock,
            definition=plugin2_definition,
            location=plugin2_location_mock
        )
    }

    assert loader.loaded_plugins == expected_plugins


def test_load_plugins_invalid_plugin_definition_type(mock_plugin_location, mock_find_plugins, context_resource_type):
    """
    Tests validation that the plugin definition is of the correct type.
    Expects the faulty plugin to be skipped and not loaded.
    """
    plugin_name = "invalid_plugin"
    plugin_definition = PluginDefinition(root_operation_name=plugin_name, resource_type=context_resource_type)

    invalid_plugin_location = mock_plugin_location(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )
    invalid_plugin_location.load_module.return_value = "This is not a PluginDefinition object"

    mock_find_plugins([invalid_plugin_location])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_plugin_definition_missing_resource_type(mock_plugin_location,
                                                              mock_find_plugins,
                                                              context_resource_type):
    """
    Tests the scenario where a plugin definition is missing the resource_type.
    Expects the plugin to be skipped and not loaded.
    """
    plugin_name = "missing_resource_type_plugin"
    plugin_definition = PluginDefinition(root_operation_name=plugin_name)

    @plugin_definition.resource_operation
    def some_operation():
        pass

    missing_resource_type_location = mock_plugin_location(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )

    mock_find_plugins([missing_resource_type_location])

    loader.load_plugins()

    assert loader.loaded_plugins == {}
