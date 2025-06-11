from pathlib import Path

import pytest

import omnitool.plugin.finder as finder
import omnitool.plugin.loader as loader
from omnitool.plugin.loader import LoadedPlugin
from omnitool.plugin.configuration import PluginConfiguration
from omnitool.plugin.data import PluginData
from omnitool.plugin.location import PluginLocation
from omnitool.plugin.definition import PluginDefinition


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

        mocker.patch.object(finder, "find_plugins", return_value=plugin_locations)

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
        load_configuration_mock = mocker.patch.object(loader, "load_configuration")
        load_configuration_mock.side_effect = configurations

        return load_configuration_mock

    return _mock_load_configuration


@pytest.fixture
def mock_load_data(mocker):
    def _mock_load_data(plugin_data_list: list[PluginData]):
        """
        Sets up the load_data mock to return the specified data.

        Args:
            plugin_data_list: List of PluginData objects to be returned.
        """
        load_data_mock = mocker.patch.object(loader, "load_data")
        load_data_mock.side_effect = plugin_data_list

        return load_data_mock

    return _mock_load_data


@pytest.fixture
def create_plugin_definition(resource_data_type) -> callable:
    def _create_plugin_definition(plugin_name: str) -> PluginDefinition:
        """
        Creates a PluginDefinition object for testing.

        Args:
            plugin_name: The name of the plugin.

        Returns:
            PluginDefinition: A PluginDefinition object with resource type and loader defined.
        """
        definition = PluginDefinition(root_operation_name=plugin_name, resource_data_type=resource_data_type)
        definition.context_loader_function = lambda c: None
        return definition

    return _create_plugin_definition


@pytest.fixture
def create_plugin(mocker, mock_plugin_location, create_plugin_definition) -> callable:
    def _create_plugin(plugin_name: str, plugin_definition: PluginDefinition = None) -> LoadedPlugin:
        """
        Creates a LoadedPlugin object with mocked components for testing.

        Args:
            plugin_name: The name of the plugin.
            plugin_definition: Optional PluginDefinition object. If not provided, one will be created.

        Returns:
            LoadedPlugin: A LoadedPlugin object with mocked location and contexts.
        """
        if plugin_definition is None:
            plugin_definition = create_plugin_definition(plugin_name)

        location_mock = mock_plugin_location(
            plugin_name=plugin_name,
            plugin_definition=plugin_definition
        )

        plugin_data = mocker.MagicMock(spec=PluginData)
        plugin_configuration = mocker.MagicMock(spec=PluginConfiguration)

        return LoadedPlugin(
            data=plugin_data,
            configuration=plugin_configuration,
            definition=plugin_definition,
            location=location_mock
        )

    return _create_plugin


def test_load_plugins_no_plugins_found(mock_find_plugins):
    """
    Tests the behavior when no plugins are available to load.
    Expects the function to log a warning and return without loading anything.
    """
    mock_find_plugins([])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_successful_loading(mocker,
                                         create_plugin,
                                         mock_find_plugins,
                                         mock_load_configuration,
                                         mock_load_data):
    """
    Tests the loading of multiple available plugins.
    Expects all plugins to be loaded correctly and stored in the loaded_plugins dictionary.
    """
    plugin1_name = "plugin1"
    plugin2_name = "plugin2"
    plugin1 = create_plugin(plugin1_name)
    plugin2 = create_plugin(plugin2_name)

    mock_find_plugins([plugin1.location, plugin2.location])
    load_configuration_mock = mock_load_configuration([plugin1.configuration, plugin2.configuration])
    load_data_mock = mock_load_data([plugin1.data, plugin2.data])

    loader.load_plugins()

    expected_plugins = {
        plugin1_name: plugin1,
        plugin2_name: plugin2
    }

    assert loader.loaded_plugins == expected_plugins

    assert load_configuration_mock.call_count == 2
    load_configuration_mock.assert_any_call(plugin1_name)
    load_configuration_mock.assert_any_call(plugin2_name)

    assert load_data_mock.call_count == 2
    load_data_mock.assert_any_call(plugin1_name, plugin1.configuration, plugin1.definition)
    load_data_mock.assert_any_call(plugin2_name, plugin2.configuration, plugin2.definition)


def test_load_plugins_multiple_plugins_with_exceptions(mocker,
                                                       create_plugin,
                                                       mock_plugin_location,
                                                       mock_find_plugins,
                                                       mock_load_configuration,
                                                       mock_load_data):
    """
    Tests loading multiple plugins where some succeed and some fail.
    Expects successful plugins to be loaded and exceptions to be handled properly
    without affecting other plugins.
    """
    good_plugin_name = "good_plugin"
    good_plugin = create_plugin(good_plugin_name)

    bad_plugin1_name = "bad_plugin1"
    bad_plugin1_location_mock = mock_plugin_location(
        plugin_name=bad_plugin1_name,
        plugin_definition=None
    )

    bad_plugin2 = create_plugin("bad_plugin2")

    mock_find_plugins([good_plugin.location, bad_plugin1_location_mock, bad_plugin2.location])
    load_configuration_mock = mock_load_configuration([
        good_plugin.configuration,
        Exception("Failed to load configuration")
    ])
    load_data_mock = mock_load_data([good_plugin.data])

    loader.load_plugins()

    expected_plugins = {
        good_plugin_name: good_plugin
    }

    assert loader.loaded_plugins == expected_plugins

    assert load_configuration_mock.call_count == 2
    load_configuration_mock.assert_any_call(good_plugin_name)
    load_configuration_mock.assert_any_call("bad_plugin2")
    assert load_data_mock.call_count == 1
    load_data_mock.assert_any_call(good_plugin_name, good_plugin.configuration, good_plugin.definition)


def test_load_plugins_all_plugins_fail(mock_plugin_location, mock_find_plugins, create_plugin_definition):
    """
    Tests the scenario where all plugins fail to load.
    Expects appropriate warning log for each plugin and an empty loaded_plugins dictionary.
    """
    bad_plugin1_name = "bad_plugin1"
    bad_plugin1_definition = create_plugin_definition(bad_plugin1_name)
    bad_plugin1_location_mock = mock_plugin_location(
        plugin_name=bad_plugin1_name,
        plugin_definition=bad_plugin1_definition
    )
    bad_plugin1_location_mock.load_module.side_effect = ValueError("Invalid plugin definition")

    bad_plugin2_name = "bad_plugin2"
    bad_plugin2_definition = create_plugin_definition(bad_plugin2_name)
    bad_plugin2_location_mock = mock_plugin_location(
        plugin_name=bad_plugin2_name,
        plugin_definition=bad_plugin2_definition
    )
    bad_plugin2_location_mock.load_module.side_effect = ImportError("Could not import plugin module")

    mock_find_plugins([bad_plugin1_location_mock, bad_plugin2_location_mock])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_resets_loaded_plugins(mocker,
                                            create_plugin,
                                            mock_find_plugins,
                                            mock_load_configuration,
                                            mock_load_data):
    """
    Tests that the global loaded_plugins dictionary is reset when the function is called.
    Expects any previously loaded plugins to be removed before loading new ones.
    """
    plugin1 = create_plugin("plugin1")
    plugin2 = create_plugin("plugin2")

    load_configuration_mock1 = mock_load_configuration([plugin1.configuration])
    mock_find_plugins([plugin1.location])

    load_data_mock1 = mock_load_data([plugin1.data])

    loader.load_plugins()

    expected_plugins = {
        "plugin1": plugin1
    }

    assert loader.loaded_plugins == expected_plugins
    load_configuration_mock1.assert_called_once_with("plugin1")
    load_data_mock1.assert_called_once_with("plugin1", plugin1.configuration, plugin1.definition)

    load_configuration_mock2 = mock_load_configuration([plugin2.configuration])
    mock_find_plugins([plugin2.location])

    load_data_mock2 = mock_load_data([plugin2.data])

    loader.load_plugins()

    expected_plugins = {
        "plugin2": plugin2
    }

    assert loader.loaded_plugins == expected_plugins
    load_configuration_mock2.assert_called_once_with("plugin2")
    load_data_mock2.assert_called_once_with("plugin2", plugin2.configuration, plugin2.definition)


def test_load_plugins_invalid_plugin_definition_type(mock_plugin_location, mock_find_plugins, create_plugin_definition):
    """
    Tests validation that the plugin definition is of the correct type.
    Expects the faulty plugin to be skipped and not loaded.
    """
    plugin_name = "invalid_plugin"
    plugin_definition = create_plugin_definition(plugin_name)

    invalid_plugin_location = mock_plugin_location(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )
    invalid_plugin_location.load_module.return_value = "This is not a PluginDefinition object"

    mock_find_plugins([invalid_plugin_location])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_plugin_definition_missing_resource_data_type(mock_plugin_location,
                                                                   mock_find_plugins):
    """
    Tests the scenario where a plugin definition is missing the resource_data_type.
    Expects the plugin to be skipped and not loaded.
    """
    plugin_name = "missing_resource_data_type_plugin"
    plugin_definition = PluginDefinition(root_operation_name=plugin_name)

    @plugin_definition.operation
    def some_operation():
        pass

    missing_resource_data_type_location = mock_plugin_location(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )

    mock_find_plugins([missing_resource_data_type_location])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_plugin_definition_missing_context_loader(mock_plugin_location,
                                                               mock_find_plugins,
                                                               resource_data_type):
    """
    Tests the validation of plugin definition context loader requirement.
    Expects the plugin to be skipped and not loaded when resource_data_type is defined but context_loader_function is missing.
    """
    plugin_name = "test_plugin"
    plugin_definition = PluginDefinition(
        root_operation_name=plugin_name,
        resource_data_type=resource_data_type
    )
    plugin_location_mock = mock_plugin_location(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )

    mock_find_plugins([plugin_location_mock])

    loader.load_plugins()

    assert loader.loaded_plugins == {}
