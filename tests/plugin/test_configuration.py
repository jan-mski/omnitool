import json
from pathlib import Path

import pytest

import omnitool.plugin.configuration
from omnitool.plugin.base import PluginLocation, PluginModule
from omnitool.plugin.configuration import (PluginConfiguration, load_configuration, PluginConfigurationLoadError,
                                           PLUGIN_CONFIGURATION_FILE_NAME)


@pytest.fixture
def mock_plugin_module(mocker):
    """
    Creates a mock PluginModule for testing.

    Returns:
        Mock: A mock PluginModule with a name property
    """
    mock_module = mocker.Mock(spec=PluginModule)
    mock_module.name = "test_plugin"

    return mock_module


@pytest.fixture
def plugin_location(mock_plugin_module):
    """
    Creates a PluginLocation for testing.

    Args:
        mock_plugin_module: A mock PluginModule

    Returns:
        PluginLocation: A PluginLocation with the mock PluginModule
    """
    return PluginLocation(plugin_module=mock_plugin_module)


@pytest.fixture
def configuration_json():
    """
    Provides a test configuration in JSON format with sample contexts and resources.

    Returns:
        dict: A nested dictionary representing plugin configuration with contexts and resources
    """
    return {
        "contexts": {
            "context1": {
                "name": "Context 1",
                "resources": {
                    "resource1": {
                        "name": "Resource 1",
                        "location": {
                            "path": "path/to/resource1",
                        },
                    },
                    "resource2": {
                        "name": "Resource 2",
                        "location": {
                            "path": "path/to/resource2",
                        },
                    },
                },
            },
            "context2": {
                "name": "Context 2",
                "resources": {
                    "resource3": {
                        "name": "Resource 3",
                        "location": {
                            "path": "path/to/resource3",
                        },
                    },
                },
            },
        },
    }


@pytest.fixture
def create_configuration_file(configuration_json):
    def _create_configuration_file(plugin_configurations_dir: Path, plugin_name: str, write: bool = True):
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

        if write:
            configuration_file.write_text(json.dumps(configuration_json))

        return configuration_file

    return _create_configuration_file


@pytest.fixture
def configuration_model(configuration_json, context_resource_type):
    """
    Creates a validated PluginConfiguration model with test data.

    Args:
        configuration_json: The test configuration data
        context_resource_type: The resource type used by the plugin

    Returns:
        PluginConfiguration: A validated configuration model with populated resource data
    """
    return PluginConfiguration.model_validate(configuration_json)


@pytest.fixture
def mock_plugin_configurations(mocker, tmp_path):
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
        mocker.patch.object(omnitool.plugin.configuration.settings, "PLUGIN_CONFIGURATIONS_PATH",
                            plugin_configurations_dir)

        for plugin_name in plugin_names:
            if not create_dirs:
                continue

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
    assert empty_configuration.resources == {}


def test_plugin_configuration_resources(configuration_json):
    """
    Tests that a PluginConfiguration correctly loads resource data from JSON.
    Expects the model dump to match the expected paths structure.
    """
    configuration_model = PluginConfiguration.model_validate(configuration_json)

    expected_paths = json.loads(json.dumps(configuration_json))  # Deep copy
    for context in expected_paths["contexts"].values():
        for resource in context["resources"].values():
            resource["location"]["path"] = Path(resource["location"]["path"])

    assert configuration_model.model_dump() == expected_paths


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
