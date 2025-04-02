from collections import OrderedDict
from importlib.metadata import EntryPoint
from pathlib import Path

import pytest

import omnitool.plugin
from omnitool.plugin.finder import PluginEntryPoint, find_plugins
from omnitool.plugin.base import PluginModule, PluginLocation


PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"


@pytest.fixture
def mock_settings(mocker):
    def _mock_settings(enabled_builtin_plugins: list[str] = None, enabled_user_plugins: list[str] = None):
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
def mock_entry_points(mocker):
    def _mock_entry_points(enabled_plugins: list[str] = None) -> dict[str, EntryPoint]:
        """
        Mocks the entry_points function in omnitool.plugin.finder for testing.

        Args:
            enabled_plugins: List of plugin names to create entry points for

        Returns:
            A dictionary mapping plugin names to their mocked EntryPoint objects
        """
        entry_points_mock = mocker.patch.object(omnitool.plugin.finder, "entry_points")

        plugin_entry_points = OrderedDict()
        for plugin_name in enabled_plugins or []:
            entry_point_mock = mocker.Mock()
            entry_point_mock.name = plugin_name
            plugin_entry_points[plugin_name] = entry_point_mock

        entry_points_mock.return_value = list(plugin_entry_points.values())

        return plugin_entry_points

    return _mock_entry_points


@pytest.fixture
def mock_plugin_configurations(mocker, tmp_path):
    def _mock_plugin_configurations(
            plugin_names: list[str] = None,
            create_dirs: bool = True,
            create_configs: bool = True,
            config_content: str = "{}"
    ) -> Path:
        """
        Sets up plugin configuration paths for testing.

        Args:
            plugin_names: List of plugin names to configure
            create_dirs: Whether to create plugin directories
            create_configs: Whether to create config files (requires create_dirs=True)
            config_content: Content to write to valid config files

        Returns:
            The base plugin configurations directory path
        """
        plugin_names = plugin_names or []

        # Set up base plugin directory
        plugin_configurations_path = tmp_path / "plugins"
        plugin_configurations_path.mkdir(parents=True, exist_ok=True)
        mocker.patch.object(omnitool.plugin.finder, "PLUGIN_CONFIGURATIONS_PATH", plugin_configurations_path)

        # Handle directory creation
        for plugin_name in plugin_names:
            if not create_dirs:
                continue

            plugin_dir = plugin_configurations_path / plugin_name
            plugin_dir.mkdir(parents=True, exist_ok=True)

            # Handle config creation
            if not create_configs:
                continue

            configuration_file = plugin_dir / PLUGIN_CONFIGURATION_FILE_NAME
            configuration_file.write_text(config_content)

        return plugin_configurations_path

    return _mock_plugin_configurations


def test_plugin_entry_point_name_property(mocker):
    """Tests that the public property name returns the underlying entry_point name.
    Expects the property to equal the entry_point name."""
    entry_point = mocker.Mock()
    entry_point.name = "test_plugin"
    plugin_entry_point = PluginEntryPoint(entry_point=entry_point)

    assert plugin_entry_point.name == "test_plugin"


def test_plugin_entry_point_load(mocker):
    """Tests that the public load method performs its functionality including calling the underlying load.
    Expects both superclass load and entry_point.load to be executed."""
    entry_point = mocker.Mock()
    plugin_entry_point = PluginEntryPoint(entry_point=entry_point)
    super_load_mock = mocker.patch.object(PluginModule, "load")

    plugin_entry_point.load()

    super_load_mock.assert_called_once()
    entry_point.load.assert_called_once()


def test_find_plugins_combines_builtin_and_user(mock_settings, mock_entry_points, mock_plugin_configurations):
    """Tests that find_plugins returns a combined list of PluginLocation objects for both builtin and user plugins
    as configured in settings.
    Expects the returned list to include properly created PluginLocation objects."""
    builtin_plugin_name = "builtin_plugin"
    user_plugin_name = "user_plugin"

    mock_settings([builtin_plugin_name], [user_plugin_name])
    plugin_entry_points = mock_entry_points([builtin_plugin_name, user_plugin_name])
    plugin_configurations_path = mock_plugin_configurations([builtin_plugin_name, user_plugin_name])

    expected_plugin_locations = [
        PluginLocation(
            configuration_file=plugin_configurations_path / builtin_plugin_name / PLUGIN_CONFIGURATION_FILE_NAME,
            plugin_module=PluginEntryPoint(plugin_entry_points[builtin_plugin_name])),
        PluginLocation(
            configuration_file=plugin_configurations_path / user_plugin_name / PLUGIN_CONFIGURATION_FILE_NAME,
            plugin_module=PluginEntryPoint(plugin_entry_points[user_plugin_name])),
    ]

    actual_plugin_locations = find_plugins()

    assert actual_plugin_locations == expected_plugin_locations


def test_find_plugins_skips_missing_plugins(mock_settings, mock_entry_points, mock_plugin_configurations, mocker):
    """Tests that find_plugins skips plugins that are not discovered in the plugin entry points.
    Expects missing plugins to be omitted with a warning logged."""
    existing_plugin_name = "existing_plugin"

    mock_settings([existing_plugin_name, "missing_plugin"], [])
    plugin_entry_points = mock_entry_points([existing_plugin_name])
    plugin_configurations_path = mock_plugin_configurations([existing_plugin_name])
    configuration_file = plugin_configurations_path / existing_plugin_name / PLUGIN_CONFIGURATION_FILE_NAME

    mock_logger = mocker.patch.object(omnitool.plugin.finder, "logger")

    expected_plugin_locations = [
        PluginLocation(configuration_file=configuration_file,
                       plugin_module=PluginEntryPoint(plugin_entry_points[existing_plugin_name]))
    ]

    actual_plugin_locations = find_plugins()

    assert actual_plugin_locations == expected_plugin_locations

    mock_logger.warning.assert_called_once()


def test_find_plugins_creates_configuration_file_if_absent(mock_settings,
                                                           mock_entry_points,
                                                           mock_plugin_configurations):
    """Tests that find_plugins causes the creation of a configuration file for a plugin when it does not exist.
    Expects a new configuration file containing "{}" to be created."""
    plugin_name = "test_plugin"

    mock_settings([plugin_name], [])
    plugin_entry_points = mock_entry_points([plugin_name])
    plugin_configurations_path = mock_plugin_configurations([plugin_name], create_configs=False)
    configuration_file = plugin_configurations_path / plugin_name / PLUGIN_CONFIGURATION_FILE_NAME

    expected_plugin_locations = [
        PluginLocation(configuration_file=configuration_file,
                       plugin_module=PluginEntryPoint(plugin_entry_points[plugin_name]))
    ]

    actual_plugin_locations = find_plugins()

    assert configuration_file.exists()
    assert configuration_file.read_text() == "{}"
    assert actual_plugin_locations == expected_plugin_locations


def test_find_plugins_ignores_invalid_configuration_directory(mock_settings,
                                                              mock_entry_points,
                                                              mock_plugin_configurations,
                                                              mocker):
    """Tests that find_plugins ignores a plugin configuration directory when it exists but is not a directory.
    Expects a warning log and PluginLocation with a None configuration file."""
    plugin_name = "test_plugin"

    mock_logger = mocker.patch.object(omnitool.plugin.finder, "logger")
    mock_settings([plugin_name], [])
    plugin_entry_points = mock_entry_points([plugin_name])
    plugin_configurations_path = mock_plugin_configurations([plugin_name], create_dirs=False)

    plugin_dir_path = plugin_configurations_path / plugin_name
    plugin_dir_path.write_text("not a directory")

    expected_plugin_locations = [
        PluginLocation(configuration_file=None,
                       plugin_module=PluginEntryPoint(plugin_entry_points[plugin_name]))
    ]

    actual_plugin_locations = find_plugins()

    assert actual_plugin_locations == expected_plugin_locations

    mock_logger.warning.assert_called_once()


def test_find_plugins_ignores_invalid_configuration_file(mock_settings,
                                                         mock_entry_points,
                                                         mock_plugin_configurations,
                                                         mocker):
    """Tests that find_plugins ignores a configuration file when it exists but is not a regular file.
    Expects a warning log and PluginLocation with a None configuration file."""
    plugin_name = "test_plugin"

    mock_logger = mocker.patch.object(omnitool.plugin.finder, "logger")
    mock_settings([plugin_name], [])
    plugin_entry_points = mock_entry_points([plugin_name])
    plugin_configurations_path = mock_plugin_configurations([plugin_name], create_configs=False)

    configuration_file = plugin_configurations_path / plugin_name / PLUGIN_CONFIGURATION_FILE_NAME
    configuration_file.mkdir()

    expected_plugin_locations = [
        PluginLocation(configuration_file=None,
                       plugin_module=PluginEntryPoint(plugin_entry_points[plugin_name]))
    ]

    actual_plugin_locations = find_plugins()

    assert actual_plugin_locations == expected_plugin_locations

    mock_logger.warning.assert_called_once()
