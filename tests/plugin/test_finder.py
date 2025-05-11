from importlib.metadata import EntryPoint

import pytest

import omnitool.plugin
from omnitool.plugin.base import PluginModule, PluginLocation
from omnitool.plugin.finder import PluginEntryPoint, find_plugins
from omnitool_plugin_base.plugin.base import PluginDefinition


@pytest.fixture
def mock_settings(mocker):
    def _mock_settings(enabled_builtin_plugins: list[str] = None, enabled_user_plugins: list[str] = None) -> None:
        """
        Mocks the settings module in omnitool.plugin.finder for testing.

        Args:
            enabled_builtin_plugins: List of builtin plugin names to enable
            enabled_user_plugins: List of user plugin names to enable

        Returns:
            None
        """
        settings_mock = mocker.patch.object(omnitool.plugin.finder, "settings")
        settings_mock.omnitool_settings.enabled_builtin_plugins = enabled_builtin_plugins or []
        settings_mock.omnitool_settings.enabled_user_plugins = enabled_user_plugins or []

    return _mock_settings


@pytest.fixture
def mock_entry_point(mocker):
    def _mock_entry_point(plugin_name: str) -> EntryPoint:
        """
        Mocks an entry point for a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            A mocked EntryPoint object
        """
        entry_point_mock = mocker.Mock()
        entry_point_mock.name = plugin_name

        return entry_point_mock

    return _mock_entry_point


@pytest.fixture
def mock_entry_points_function(mocker, mock_entry_point):
    def _mock_entry_points_function(plugin_entry_points: list[EntryPoint]) -> None:
        entry_points_mock = mocker.patch.object(omnitool.plugin.finder, "entry_points")
        entry_points_mock.return_value = list(plugin_entry_points)

    return _mock_entry_points_function


@pytest.fixture
def mock_entry_points(mock_entry_point, mock_entry_points_function):
    def _mock_entry_points(enabled_plugins: list[str] = None) -> dict[str, EntryPoint]:
        """
        Mocks the entry_points function in omnitool.plugin.finder for testing.

        Args:
            enabled_plugins: List of plugin names to create entry points for

        Returns:
            A dictionary mapping plugin names to their mocked EntryPoint objects
        """
        plugin_entry_points = {}
        for plugin_name in enabled_plugins or []:
            entry_point_mock = mock_entry_point(plugin_name)
            plugin_entry_points[plugin_name] = entry_point_mock

        mock_entry_points_function(list(plugin_entry_points.values()))

        return plugin_entry_points

    return _mock_entry_points


def test_plugin_entry_point_name_property(mocker):
    """
    Tests that the public property name returns the underlying entry_point name.
    Expects the property to equal the entry_point name.
    """
    entry_point = mocker.Mock()
    entry_point.name = "test_plugin"
    plugin_entry_point = PluginEntryPoint(entry_point=entry_point)

    assert plugin_entry_point.name == "test_plugin"


def test_plugin_entry_point_load(mocker, context_resource_type):
    """
    Tests that the public load method performs its functionality including calling the underlying load.
    Expects both superclass load and entry_point.load to be executed.
    """
    entry_point = mocker.Mock()
    plugin_definition = PluginDefinition(root_operation_name="test_plugin", resource_type=context_resource_type)
    entry_point.load.return_value = plugin_definition
    plugin_entry_point = PluginEntryPoint(entry_point=entry_point)
    super_load_mock = mocker.patch.object(PluginModule, "load")

    loaded_plugin_definition = plugin_entry_point.load()

    assert loaded_plugin_definition == plugin_definition

    super_load_mock.assert_called_once()
    entry_point.load.assert_called_once()


def test_find_plugins_combines_builtin_and_user(mock_settings, mock_entry_points):
    """
    Tests that find_plugins returns a combined list of PluginLocation objects for both builtin and user plugins
    as configured in settings.
    Expects the returned list to include properly created PluginLocation objects.
    """
    builtin_plugin_name = "builtin_plugin"
    user_plugin_name = "user_plugin"

    mock_settings([builtin_plugin_name], [user_plugin_name])
    plugin_entry_points = mock_entry_points([builtin_plugin_name, user_plugin_name])

    expected_plugin_locations = [
        PluginLocation(
            plugin_module=PluginEntryPoint(plugin_entry_points[builtin_plugin_name])),
        PluginLocation(
            plugin_module=PluginEntryPoint(plugin_entry_points[user_plugin_name])),
    ]

    actual_plugin_locations = find_plugins()

    assert actual_plugin_locations == expected_plugin_locations


def test_find_plugins_skips_missing_plugins(mock_settings, mock_entry_points):
    """
    Tests that find_plugins skips plugins that are not discovered in the plugin entry points.
    Expects missing plugins to be omitted.
    """
    existing_plugin_name = "existing_plugin"

    mock_settings([existing_plugin_name, "missing_plugin"], [])
    plugin_entry_points = mock_entry_points([existing_plugin_name])

    expected_plugin_locations = [
        PluginLocation(plugin_module=PluginEntryPoint(plugin_entry_points[existing_plugin_name]))
    ]

    actual_plugin_locations = find_plugins()

    assert actual_plugin_locations == expected_plugin_locations


def test_find_plugins_handles_duplicate_plugin_name(mock_settings,
                                                    mock_entry_point,
                                                    mock_entry_points_function):
    """
    Tests that find_plugins correctly handles a plugin name that appears in both builtin and user plugin lists.
    Expects the plugin to appear only once in the final list.
    """
    duplicate_plugin_name = "duplicate_plugin"

    mock_settings([duplicate_plugin_name], [duplicate_plugin_name])
    first_entry_point = mock_entry_point(duplicate_plugin_name)
    second_entry_point = mock_entry_point(duplicate_plugin_name)
    mock_entry_points_function([first_entry_point, second_entry_point])

    expected_plugin_locations = [
        PluginLocation(
            plugin_module=PluginEntryPoint(first_entry_point)),
    ]

    actual_plugin_locations = find_plugins()

    assert len(actual_plugin_locations) == 1
    assert actual_plugin_locations == expected_plugin_locations
