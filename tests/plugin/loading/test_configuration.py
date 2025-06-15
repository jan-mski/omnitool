from pathlib import Path

import pytest

import omnitool.settings as settings
from omnitool.plugin.loading.location import PluginModule, PluginLocation
from omnitool.plugin.loading.configuration import (PluginConfiguration, load_configuration, PluginConfigurationLoadError,
                                          PLUGIN_CONFIGURATION_FILE_NAME)


@pytest.fixture
def mock_plugin_module(mocker) -> PluginModule:
    """
    Creates a mock PluginModule for testing.

    Returns:
        Mock: A mock PluginModule with a name property
    """
    mock_module = mocker.Mock(spec=PluginModule)
    mock_module.name = "test_plugin"

    return mock_module


@pytest.fixture
def plugin_location(mock_plugin_module) -> PluginLocation:
    """
    Creates a PluginLocation for testing.

    Args:
        mock_plugin_module: A mock PluginModule

    Returns:
        PluginLocation: A PluginLocation with the mock PluginModule
    """
    return PluginLocation(plugin_module=mock_plugin_module)


@pytest.fixture
def create_configuration_file(configuration_json) -> callable:
    def _create_configuration_file(plugin_configurations_dir: Path, plugin_name: str, write: bool = True) -> Path:
        """
        Creates a temporary configuration file for testing.

        Args:
            plugin_configurations_dir: The base directory for plugin configurations
            plugin_name: The name of the plugin
            write: Whether to write the configuration JSON to the file (default: True)

        Returns:
            Path: Path to the created configuration file
        """
        configuration_file = plugin_configurations_dir / plugin_name / PLUGIN_CONFIGURATION_FILE_NAME
        configuration_file.parent.mkdir(parents=True, exist_ok=True)

        if write:
            configuration_file.write_text(configuration_json, encoding="utf-8")

        return configuration_file

    return _create_configuration_file


@pytest.fixture
def mock_plugin_configurations(mocker, tmp_path) -> callable:
    def _mock_plugin_configurations(plugin_names: list[str] = None, create_dirs: bool = True) -> Path:
        """
        Sets up plugin configuration paths for testing.

        Args:
            plugin_names: List of plugin names to configure
            create_dirs: Whether to create plugin directories

        Returns:
            The base plugin configurations directory path
        """
        plugin_names = plugin_names or []

        plugin_configurations_dir = tmp_path / "plugins"
        plugin_configurations_dir.mkdir(parents=True, exist_ok=True)
        mocker.patch.object(settings, "PLUGIN_CONFIGURATIONS_PATH", plugin_configurations_dir)

        if create_dirs:
            for plugin_name in plugin_names:
                plugin_dir = plugin_configurations_dir / plugin_name
                plugin_dir.mkdir(parents=True, exist_ok=True)

        return plugin_configurations_dir

    return _mock_plugin_configurations


def test_plugin_configuration_empty():
    """
    Tests that an empty PluginConfiguration can be created.
    Expects empty dictionaries for contexts and resources.
    """
    empty_configuration = PluginConfiguration()

    assert empty_configuration.contexts == {}


def test_plugin_configuration_resources(configuration_json, configuration_model):
    """
    Tests that a PluginConfiguration correctly loads resource data from JSON.
    Expects the model dump to match the expected paths structure.
    """
    actual_configuration = PluginConfiguration.model_validate_json(configuration_json)

    assert actual_configuration == configuration_model


def test_load_configuration(create_configuration_file, configuration_model, mock_plugin_configurations):
    """
    Tests that configuration loading works correctly.
    Expects the loaded configuration to match the expected model.
    """
    plugin_name = "test_plugin"

    plugin_configurations_dir = mock_plugin_configurations([plugin_name])
    create_configuration_file(plugin_configurations_dir, plugin_name)

    loaded_configuration = load_configuration(plugin_name)

    assert loaded_configuration == configuration_model


def test_load_configuration_nonexistent_file(create_configuration_file, mock_plugin_configurations):
    """
    Tests that loading from a nonexistent file creates a default configuration.
    Expects an empty configuration to be created and the configuration file to be written.
    """
    default_plugin_configuration = PluginConfiguration()
    expected_file_content = default_plugin_configuration.model_dump_json(indent=2)
    plugin_name = "test_plugin"

    plugin_configurations_dir = mock_plugin_configurations([plugin_name])
    configuration_file = create_configuration_file(plugin_configurations_dir, plugin_name, write=False)

    configuration = load_configuration(plugin_name)

    assert configuration.contexts == {}
    assert configuration_file.is_file()
    assert configuration_file.read_text(encoding="utf-8") == expected_file_content


def test_load_configuration_not_a_file(mock_plugin_configurations):
    """
    Tests that loading from a path that is not a file raises an exception.
    Expects the exception to be raised when the configuration path is a directory.
    """
    plugin_name = "test_plugin"

    plugin_configurations_dir = mock_plugin_configurations([plugin_name])
    (plugin_configurations_dir / plugin_name / PLUGIN_CONFIGURATION_FILE_NAME).mkdir()

    with pytest.raises(PluginConfigurationLoadError):
        load_configuration(plugin_name)


def test_load_configuration_not_a_directory(mock_plugin_configurations):
    """
    Tests that find_plugins ignores a plugin configuration directory when it exists but is not a directory.
    Expects the exception to be raised when the configuration path is not a directory.
    """
    plugin_name = "test_plugin"

    plugin_configurations_path = mock_plugin_configurations([plugin_name], create_dirs=False)

    plugin_dir_path = plugin_configurations_path / plugin_name
    plugin_dir_path.write_text("not a directory")

    with pytest.raises(PluginConfigurationLoadError):
        load_configuration(plugin_name)
