import json
from pathlib import Path

import pytest

from omnitool.plugin.configuration import PluginConfiguration, load_configuration, PluginConfigurationLoadError


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
def create_configuration_file(tmp_path, configuration_json):
    def _create_configuration_file(write: bool = True):
        """
        Creates a temporary configuration file for testing.

        Args:
            write: Whether to write the configuration JSON to the file (default: True)

        Returns:
            Path: Path to the created configuration file
        """
        configuration_file = tmp_path / "configuration.json"

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


def test_load_configuration(create_configuration_file, configuration_model):
    """
    Tests that configuration loading works correctly.
    Expects the loaded configuration to match the expected model.
    """
    loaded_configuration = load_configuration(create_configuration_file())

    assert loaded_configuration == configuration_model


def test_load_configuration_nonexistent_file(create_configuration_file, configuration_model):
    """
    Tests that loading from a nonexistent file creates a default configuration.
    Expects an empty configuration to be created and the configuration file to be written.
    """
    configuration_file = create_configuration_file(write=False)
    default_plugin_configuration = PluginConfiguration()
    expected_file_content = default_plugin_configuration.model_dump_json(indent=2)

    configuration = load_configuration(configuration_file=configuration_file)

    assert configuration.contexts == {}
    assert configuration_file.is_file()
    assert configuration_file.read_text(encoding="utf-8") == expected_file_content


def test_load_configuration_not_a_file(tmp_path, context_resource_type):
    """
    Tests that loading from a path that is not a file raises an exception.
    Expects the exception to be raised when the configuration path is a directory.
    """
    configuration_dir = tmp_path / "config_dir"
    configuration_dir.mkdir()

    with pytest.raises(PluginConfigurationLoadError) as exc_info:
        load_configuration(configuration_file=configuration_dir)

    assert f"Configuration file '{configuration_dir}' is not a file" in str(exc_info.value)
