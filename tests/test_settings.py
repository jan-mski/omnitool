import json
from pathlib import Path
from typing import Optional

import pytest
from pydantic import ValidationError

import omnitool.settings as settings_module


@pytest.fixture
def mock_settings_file(mocker):
    def _mock_settings_file(home_path: Path, content: Optional[str] = None, create_home_path: bool = True) -> Path:
        """
        Creates and configures a mock settings file.

        Args:
            home_path: Path to use as the Omnitool home directory
            content: Optional JSON content to write to the settings file
            create_home_path: Whether to create the home path directory

        Returns:
            Path object pointing to the mocked settings file
        """
        if create_home_path:
            home_path.mkdir(parents=True, exist_ok=True)

        settings_file_mock = home_path / "settings.json"
        mocker.patch.object(settings_module, "OMNITOOL_HOME_PATH", home_path)
        mocker.patch.object(settings_module, "OMNITOOL_SETTINGS_FILE_PATH", settings_file_mock)

        if content is not None:
            settings_file_mock.write_text(content)

        return settings_file_mock

    return _mock_settings_file


@pytest.fixture
def mock_default_plugins(mocker):
    def _mock_default_plugins(builtin_plugins: list[str]):
        """
        Mocks the built-in plugin names with the provided list.
        
        Args:
            builtin_plugins: List of plugin names to use as built-in plugins
        """
        mocker.patch.object(settings_module, "BUILTIN_PLUGIN_NAMES", builtin_plugins)

    return _mock_default_plugins


@pytest.mark.parametrize("default, enabled", [
    ("plugin_1", ["plugin_1", "plugin_2"]),  # Default in enabled list
    (None, ["plugin_1", "plugin_2"]),        # No default specified
], ids=["default_in_enabled", "no_default"])
def test_configured_plugins_valid(default: str, enabled: list[str]):
    """
    Tests creating ConfiguredPlugins with valid configurations.
    Validates both when default is in enabled list and when no default is specified.
    """
    plugins = settings_module.ConfiguredPlugins(default=default, enabled=enabled)

    assert plugins.default == default
    assert plugins.enabled == enabled


@pytest.mark.parametrize("default, enabled", [
    ("plugin_3", ["plugin_1", "plugin_2"]),  # Default not in enabled list
    (None, []),                              # Empty enabled list
], ids=["default_not_in_enabled", "empty_enabled_list"])
def test_configured_plugins_invalid(default: str, enabled: list[str]):
    """
    Tests that ConfiguredPlugins validation raises errors for invalid configurations.
    Validates both when default plugin is not in the enabled list and when the enabled list is empty. """
    with pytest.raises(ValidationError):
        settings_module.ConfiguredPlugins(default=default, enabled=enabled)


def test_configured_plugins_fields_are_immutable():
    """
    Tests that fields default and enabled cannot be modified after creation.
    Expects ValidationError when attempting to change these fields.
    """
    enabled_plugins = ["plugin_1", "plugin_2"]
    default_plugin = "plugin_1"

    plugins = settings_module.ConfiguredPlugins(default=default_plugin, enabled=enabled_plugins)

    with pytest.raises(ValidationError):
        plugins.default = "plugin_2"

    with pytest.raises(ValidationError):
        plugins.enabled = ["plugin_2"]


def test_omnitool_settings_valid():
    """
    Tests that OmnitoolSettings can be inherited from while maintaining base functionality.
    Expects child classes to retain validation and loading behaviors.
    """
    enabled_plugins = ["plugin_1", "plugin_2"]
    default_plugin = "plugin_1"
    settings_data = {
        "plugins": {
            "default": default_plugin,
            "enabled": enabled_plugins
        }
    }

    omnitool_settings = settings_module._OmnitoolSettings.model_validate(settings_data)

    assert omnitool_settings.model_dump() == settings_data


def test_omnitool_settings_invalid():
    """
    Tests that OmnitoolSettings can be inherited from while maintaining base functionality.
    Expects child classes to retain validation and loading behaviors.
    """
    with pytest.raises(ValidationError):
        settings_module._OmnitoolSettings.model_validate({})


def test_load_settings_valid_file(tmp_path, mock_settings_file, mock_default_plugins):
    """
    Tests loading settings from a valid file and updating global settings variable.
    Expects successful return of settings object and global variable to be updated.
    """
    enabled_plugins = ["plugin_1", "plugin_2"]
    default_plugin = "plugin_1"

    mock_settings_file(tmp_path, json.dumps({
        "plugins": {
            "default": default_plugin,
            "enabled": enabled_plugins
        }
    }))

    expected_omnitool_settings = settings_module._OmnitoolSettings(
        plugins=settings_module.ConfiguredPlugins(default=default_plugin, enabled=enabled_plugins))

    omnitool_settings = settings_module.load_settings()

    assert omnitool_settings == expected_omnitool_settings
    assert settings_module.omnitool_settings == expected_omnitool_settings


def test_load_settings_creates_default_file(tmp_path, mock_settings_file, mock_default_plugins):
    """
    Tests creating a default settings file with expected values when file doesn't exist.
    Expects file creation with git plugin enabled and set as default.
    """
    enabled_plugins = ["plugin_1", "plugin_2"]
    default_plugin = "plugin_1"

    mock_default_plugins(enabled_plugins)
    settings_file_mock = mock_settings_file(tmp_path / ".omnitool")

    expected_omnitool_settings = settings_module._OmnitoolSettings(
        plugins=settings_module.ConfiguredPlugins(default=default_plugin, enabled=enabled_plugins))

    settings_module.load_settings()

    assert settings_file_mock.exists()

    omnitool_settings = settings_module._OmnitoolSettings.model_validate_json(settings_file_mock.read_text())

    assert omnitool_settings == expected_omnitool_settings
    assert settings_module.omnitool_settings == expected_omnitool_settings


def test_load_settings_creates_directory_and_file(tmp_path, mock_settings_file, mock_default_plugins):
    """
    Tests creating both directory and settings file when neither exists.
    Expects both directory and file to be created with proper settings content.
    """
    enabled_plugins = ["plugin_1", "plugin_2"]
    default_plugin = "plugin_1"
    nonexistent_dir = tmp_path / "nonexistent_dir" / ".omnitool"

    mock_default_plugins(enabled_plugins)
    settings_file_mock = mock_settings_file(nonexistent_dir, create_home_path=False)

    expected_omnitool_settings = settings_module._OmnitoolSettings(
        plugins=settings_module.ConfiguredPlugins(default=default_plugin, enabled=enabled_plugins))

    settings_module.load_settings()

    assert nonexistent_dir.exists()
    assert nonexistent_dir.is_dir()
    assert settings_file_mock.exists()
    assert settings_file_mock.is_file()

    omnitool_settings = settings_module._OmnitoolSettings.model_validate_json(settings_file_mock.read_text())

    assert omnitool_settings == expected_omnitool_settings


def test_load_settings_raises_error_permission_denied_when_creating_default_file(tmp_path, mock_settings_file, mocker):
    """
    Tests proper handling of permission errors when writing default settings.
    Expects OmnitoolSettingsLoadError wrapping the permission error.
    """
    mock_settings_file(tmp_path / "settings.json")

    open_mock = mocker.mock_open()
    open_mock.side_effect = PermissionError("Permission denied")

    mocker.patch('io.open', open_mock)

    with pytest.raises(settings_module.OmnitoolSettingsLoadError) as exc:
        settings_module.load_settings()

    assert type(exc.value.__cause__) is PermissionError


def test_load_settings_raises_error_when_path_not_a_file(tmp_path, mock_settings_file):
    """
    Tests raising error when settings path exists but is not a file.
    Expects OmnitoolSettingsLoadError to be raised.
    """
    settings_file_mock = mock_settings_file(tmp_path)
    settings_file_mock.mkdir()

    with pytest.raises(settings_module.OmnitoolSettingsLoadError) as exc:
        settings_module.load_settings()

    assert "does not point to a file" in str(exc.value)


def test_load_settings_raises_error_when_invalid_content(tmp_path, mock_settings_file):
    """
    Tests raising error when settings file contains invalid JSON or structure.
    Expects OmnitoolSettingsLoadError wrapping the original exception.
    """
    mock_settings_file(tmp_path, "{ this is not valid json }")

    with pytest.raises(settings_module.OmnitoolSettingsLoadError) as exc:
        settings_module.load_settings()

    assert type(exc.value.__cause__) is ValidationError


def test_load_settings_raises_error_permission_denied_when_reading_file(tmp_path, mock_settings_file, mocker):
    """
    Tests proper handling of permission errors when reading settings.
    Expects OmnitoolSettingsLoadError wrapping the permission error.
    """
    mock_settings_file(tmp_path, "{}")

    open_mock = mocker.mock_open()
    open_mock.side_effect = PermissionError("Permission denied")

    mocker.patch('io.open', open_mock)

    with pytest.raises(settings_module.OmnitoolSettingsLoadError) as exc:
        settings_module.load_settings()

    assert type(exc.value.__cause__) is PermissionError
