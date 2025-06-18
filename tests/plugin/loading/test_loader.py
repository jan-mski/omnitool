import pytest

import omnitool.plugin.loading.finder as finder
import omnitool.plugin.loading.loader as loader
from omnitool.plugin.api.definition import PluginDefinition
from omnitool.plugin.loading.configuration import PluginConfiguration
from omnitool.plugin.loading.data import PluginData
from omnitool.plugin.loading.loader import LoadedPlugin
from omnitool.plugin.loading.location import PluginModule


@pytest.fixture
def mock_find_plugins(mocker) -> callable:
    def _mock_find_plugins(plugin_modules: list[PluginModule] = None):
        """
        Sets up the find_plugins mock to return the specified plugin modules.

        Args:
            plugin_modules: List of plugin module mocks to be returned by find_plugins.
                            Defaults to an empty list if None is provided.

        Returns:
            MagicMock: The patched find_plugins mock object.
        """
        if plugin_modules is None:
            plugin_modules = []

        mocker.patch.object(finder, "find_plugins", return_value=plugin_modules)

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
def plugin_data_mock(mocker) -> PluginData:
    """
    Creates a mock PluginData for testing.

    Returns:
        MagicMock: A mocked PluginData instance
    """
    return mocker.MagicMock(spec=PluginData)


def test_loaded_plugin(create_plugin_definition, mock_plugin_module, plugin_data_mock):
    """
    Tests that the plugin's name property correctly returns the name from the plugin definition.
    Expects the plugin name to match the name in the plugin definition.
    """
    plugin_name = "test_plugin"
    plugin_definition = create_plugin_definition(plugin_name)
    plugin_module_mock = mock_plugin_module(plugin_name, plugin_definition)

    loaded_plugin = LoadedPlugin(data=plugin_data_mock,
                                 definition=plugin_definition,
                                 module=plugin_module_mock)

    assert loaded_plugin.name == plugin_name
    assert loaded_plugin.definition == plugin_definition
    assert loaded_plugin.module == plugin_module_mock
    assert loaded_plugin.data == plugin_data_mock


def test_load_plugins_no_plugins_found(mock_find_plugins):
    """
    Tests the behavior when no plugins are available to load.
    Expects the function to log a warning and return without loading anything.
    """
    mock_find_plugins([])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_successful_loading(create_loaded_plugin,
                                         mock_find_plugins,
                                         mock_load_configuration,
                                         mock_load_data,
                                         create_configuration_model):
    """
    Tests the loading of multiple available plugins.
    Expects all plugins to be loaded correctly and stored in the loaded_plugins dictionary.
    """
    plugin1_name = "plugin1"
    plugin2_name = "plugin2"
    plugin1 = create_loaded_plugin(plugin1_name)
    plugin2 = create_loaded_plugin(plugin2_name)

    plugin1_configuration_mock = create_configuration_model()
    plugin2_configuration_mock = create_configuration_model()

    mock_find_plugins([plugin1.module, plugin2.module])
    load_configuration_mock = mock_load_configuration([plugin1_configuration_mock, plugin2_configuration_mock])
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
    load_data_mock.assert_any_call(plugin1_name, plugin1_configuration_mock, plugin1.definition)
    load_data_mock.assert_any_call(plugin2_name, plugin2_configuration_mock, plugin2.definition)


def test_load_plugins_multiple_plugins_with_exceptions(create_loaded_plugin,
                                                       mock_plugin_module,
                                                       mock_find_plugins,
                                                       mock_load_configuration,
                                                       mock_load_data,
                                                       create_configuration_model,
                                                       create_plugin_definition):
    """
    Tests loading multiple plugins where some succeed and some fail.
    Expects successful plugins to be loaded and exceptions to be handled properly
    without affecting other plugins.
    """
    good_plugin_name = "good_plugin"
    good_plugin = create_loaded_plugin(good_plugin_name)
    good_plugin_configuration_mock = create_configuration_model()

    bad_plugin1_name = "bad_plugin1"
    bad_plugin1_module_mock = mock_plugin_module(
        plugin_name=bad_plugin1_name,
        plugin_definition=None
    )

    bad_plugin2_name = "bad_plugin2"
    bad_plugin2_definition = create_plugin_definition(bad_plugin2_name)
    bad_plugin2_module_mock = mock_plugin_module(
        plugin_name=bad_plugin2_name,
        plugin_definition=bad_plugin2_definition
    )

    mock_find_plugins([good_plugin.module, bad_plugin1_module_mock, bad_plugin2_module_mock])
    load_configuration_mock = mock_load_configuration([
        good_plugin_configuration_mock,
        Exception("Failed to load configuration for bad_plugin2")
    ])
    load_data_mock = mock_load_data([good_plugin.data])

    loader.load_plugins()

    expected_plugins = {
        good_plugin_name: good_plugin
    }

    assert loader.loaded_plugins == expected_plugins

    assert load_configuration_mock.call_count == 2
    load_configuration_mock.assert_any_call(good_plugin_name)
    load_configuration_mock.assert_any_call(bad_plugin2_name)

    assert load_data_mock.call_count == 1
    load_data_mock.assert_any_call(good_plugin_name, good_plugin_configuration_mock, good_plugin.definition)


def test_load_plugins_all_plugins_fail(mock_plugin_module, mock_find_plugins, create_plugin_definition):
    """
    Tests the scenario where all plugins fail to load.
    Expects appropriate warning log for each plugin and an empty loaded_plugins dictionary.
    """
    bad_plugin1_name = "bad_plugin1"
    bad_plugin1_definition = create_plugin_definition(bad_plugin1_name)
    bad_plugin1_module_mock = mock_plugin_module(
        plugin_name=bad_plugin1_name,
        plugin_definition=bad_plugin1_definition
    )
    bad_plugin1_module_mock.load.side_effect = ValueError("Invalid plugin definition")

    bad_plugin2_name = "bad_plugin2"
    bad_plugin2_definition = create_plugin_definition(bad_plugin2_name)
    bad_plugin2_module_mock = mock_plugin_module(
        plugin_name=bad_plugin2_name,
        plugin_definition=bad_plugin2_definition
    )
    bad_plugin2_module_mock.load.side_effect = ImportError("Could not import plugin module")

    mock_find_plugins([bad_plugin1_module_mock, bad_plugin2_module_mock])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_resets_loaded_plugins(create_loaded_plugin,
                                            mock_find_plugins,
                                            mock_load_configuration,
                                            mock_load_data,
                                            create_configuration_model):
    """
    Tests that the global loaded_plugins dictionary is reset when the function is called.
    Expects any previously loaded plugins to be removed before loading new ones.
    """
    plugin1 = create_loaded_plugin("plugin1")
    plugin1_configuration_mock = create_configuration_model()
    plugin2 = create_loaded_plugin("plugin2")
    plugin2_configuration_mock = create_configuration_model()

    mock_find_plugins([plugin1.module])
    load_configuration_mock1 = mock_load_configuration([plugin1_configuration_mock])
    load_data_mock1 = mock_load_data([plugin1.data])

    loader.load_plugins()

    expected_plugins1 = {
        "plugin1": plugin1
    }

    assert loader.loaded_plugins == expected_plugins1
    load_configuration_mock1.assert_called_once_with("plugin1")
    load_data_mock1.assert_called_once_with("plugin1", plugin1_configuration_mock, plugin1.definition)

    mock_find_plugins([plugin2.module])
    load_configuration_mock2 = mock_load_configuration([plugin2_configuration_mock])
    load_data_mock2 = mock_load_data([plugin2.data])


    loader.load_plugins()

    expected_plugins2 = {
        "plugin2": plugin2
    }

    assert loader.loaded_plugins == expected_plugins2
    load_configuration_mock2.assert_called_once_with("plugin2")
    load_data_mock2.assert_called_once_with("plugin2", plugin2_configuration_mock, plugin2.definition)


def test_load_plugins_invalid_plugin_definition_type(mock_plugin_module, mock_find_plugins, create_plugin_definition):
    """
    Tests validation that the plugin definition is of the correct type.
    Expects the faulty plugin to be skipped and not loaded.
    """
    plugin_name = "invalid_plugin"
    plugin_definition = create_plugin_definition(plugin_name)

    invalid_plugin_module = mock_plugin_module(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )
    invalid_plugin_module.load.return_value = "This is not a PluginDefinition object"

    mock_find_plugins([invalid_plugin_module])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_plugin_definition_missing_resource_data_type(mock_plugin_module,
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

    missing_resource_data_type_module = mock_plugin_module(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )

    mock_find_plugins([missing_resource_data_type_module])

    loader.load_plugins()

    assert loader.loaded_plugins == {}


def test_load_plugins_plugin_definition_missing_context_loader(mock_plugin_module,
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
    plugin_module_mock = mock_plugin_module(
        plugin_name=plugin_name,
        plugin_definition=plugin_definition
    )

    mock_find_plugins([plugin_module_mock])

    loader.load_plugins()

    assert loader.loaded_plugins == {}
