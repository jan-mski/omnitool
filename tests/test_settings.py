from pathlib import Path
from typing import Optional

import pytest
import json

import omnitool.settings as settings_module
from pydantic import ValidationError


@pytest.fixture
def mock_settings_file(monkeypatch):
    def _mock_settings_file(home_path: Path, content: Optional[str] = None, create_home_path: bool = True) -> Path:
        if create_home_path:
            home_path.mkdir(parents=True, exist_ok=True)

        settings_file_mock = home_path / "settings.json"
        monkeypatch.setattr(settings_module, "OMNITOOL_HOME_PATH", home_path)
        monkeypatch.setattr(settings_module, "OMNITOOL_SETTINGS_FILE_PATH", settings_file_mock)

        if content is not None:
            settings_file_mock.write_text(content)

        return settings_file_mock

    return _mock_settings_file


@pytest.fixture
def mock_default_plugins(monkeypatch):
    def _mock_default_plugins(default_plugins: list):
        monkeypatch.setattr(settings_module, "DEFAULT_ENABLED_PLUGIN_NAMES", default_plugins)

    return _mock_default_plugins


@pytest.mark.parametrize("default, enabled", [
    ("plugin_1", ["plugin_1", "plugin_2"]),  # Default in enabled list
    (None, ["plugin_1", "plugin_2"]),        # No default specified
], ids=["with_default", "no_default"])
def test_configured_plugins_valid(default, enabled):
    """Tests creating ConfiguredPlugins with valid configurations.
    Validates both when default is in enabled list and when no default is specified."""
    plugins = settings_module.ConfiguredPlugins(default=default, enabled=enabled)

    assert plugins.default == default
    assert plugins.enabled == enabled


@pytest.mark.parametrize("default, enabled", [
    ("plugin_3", ["plugin_1", "plugin_2"]),  # Default not in enabled list
    (None, []),                              # Empty enabled list
], ids=["default_not_in_enabled", "empty_enabled_list"])
def test_configured_plugins_validation_errors(default, enabled):
    """Tests that ConfiguredPlugins validation raises errors for invalid configurations.
    Validates both when default plugin is not in the enabled list and when the enabled list is empty. """
    with pytest.raises(ValidationError):
        settings_module.ConfiguredPlugins(default=default, enabled=enabled)


def test_configured_plugins_fields_are_immutable():
    """Tests that fields default and enabled cannot be modified after creation.
    Expects ValidationError when attempting to change these fields."""
    plugins = settings_module.ConfiguredPlugins(default="plugin_1", enabled=["plugin_1", "plugin_2"])

    with pytest.raises(ValidationError):
        plugins.default = "plugin_2"

    with pytest.raises(ValidationError):
        plugins.enabled = ["plugin_2"]


def test_load_settings_valid_file(tmp_path, mock_settings_file, mock_default_plugins):
    """Tests loading settings from a valid file and updating global settings variable.
    Expects successful return of settings object and global variable to be updated."""
    default_plugins = ["plugin_1", "plugin_2"]
    mock_default_plugins(default_plugins)
    mock_settings_file(tmp_path, json.dumps({
        "plugins": {
            "default": "plugin_1",
            "enabled": default_plugins
        }
    }))
    expected_omnitool_settings = settings_module._OmnitoolSettings(
        plugins=settings_module.ConfiguredPlugins(default="plugin_1", enabled=default_plugins))

    omnitool_settings = settings_module.load_settings()

    assert omnitool_settings == expected_omnitool_settings
    assert settings_module.omnitool_settings == expected_omnitool_settings


def test_load_settings_creates_default_file(tmp_path, mock_settings_file, mock_default_plugins):
    """Tests creating a default settings file with expected values when file doesn't exist.
    Expects file creation with git plugin enabled and set as default."""
    default_plugins = ["plugin_1", "plugin_2"]
    mock_default_plugins(default_plugins)
    settings_file_mock = mock_settings_file(tmp_path / ".omnitool")
    expected_omnitool_settings = settings_module._OmnitoolSettings(
        plugins=settings_module.ConfiguredPlugins(default="plugin_1", enabled=default_plugins))

    assert not settings_file_mock.exists()

    settings_module.load_settings()

    assert settings_file_mock.exists()

    omnitool_settings = settings_module._OmnitoolSettings.model_validate_json(settings_file_mock.read_text())

    assert omnitool_settings == expected_omnitool_settings


def test_load_settings_creates_directory_and_file(tmp_path, mock_settings_file, mock_default_plugins):
    """Tests creating both directory and settings file when neither exists.
    Expects both directory and file to be created with proper settings content."""
    default_plugins = ["plugin_1", "plugin_2"]
    nonexistent_dir = tmp_path / "nonexistent_dir" / ".omnitool"
    mock_default_plugins(default_plugins)
    settings_file_mock = mock_settings_file(nonexistent_dir, create_home_path=False)
    expected_omnitool_settings = settings_module._OmnitoolSettings(
        plugins=settings_module.ConfiguredPlugins(default="plugin_1", enabled=default_plugins))
    
    assert not nonexistent_dir.exists()

    settings_module.load_settings()

    assert nonexistent_dir.exists()
    assert nonexistent_dir.is_dir()
    assert settings_file_mock.exists()
    assert settings_file_mock.is_file()

    omnitool_settings = settings_module._OmnitoolSettings.model_validate_json(settings_file_mock.read_text())

    assert omnitool_settings == expected_omnitool_settings


def test_load_settings_error_path_not_a_file(tmp_path, monkeypatch):
    """Tests raising error when settings path exists but is not a file.
    Expects OmnitoolSettingsLoadError to be raised."""
    settings_file_mock = tmp_path / "settings.json"
    settings_file_mock.mkdir()

    monkeypatch.setattr(settings_module, "OMNITOOL_SETTINGS_FILE_PATH", settings_file_mock)

    with pytest.raises(settings_module.OmnitoolSettingsLoadError) as exc:
        settings_module.load_settings()

    assert "does not point to a file" in str(exc.value)


def test_load_settings_error_invalid_content(tmp_path, mock_settings_file):
    """Tests raising error when settings file contains invalid JSON or structure.
    Expects OmnitoolSettingsLoadError wrapping the original exception."""
    mock_settings_file(tmp_path, "{ this is not valid json }")

    with pytest.raises(settings_module.OmnitoolSettingsLoadError):
        settings_module.load_settings()


def test_load_settings_error_permission_denied(tmp_path, mock_settings_file, mocker):
    """Tests proper handling of permission errors when reading/writing settings.
    Expects OmnitoolSettingsLoadError wrapping the permission error."""
    mock_settings_file(tmp_path, "{}")

    open_mock = mocker.mock_open(read_data='scribble')
    open_mock.side_effect = PermissionError("Permission denied")

    mocker.patch('io.open', open_mock)

    with pytest.raises(settings_module.OmnitoolSettingsLoadError) as exc:
        settings_module.load_settings()

    assert type(exc.value.__cause__) is PermissionError


def test_settings_inheritance_behavior():
    """Tests that OmnitoolSettings can be inherited from while maintaining base functionality.
    Expects child classes to retain validation and loading behaviors."""

    class CustomSettings(settings_module.OmnitoolSettings):
        pass

    settings_data = {
        "plugins": {
            "default": "plugin_1",
            "enabled": ["plugin_1", "plugin_2"]
        }
    }

    settings = CustomSettings.model_validate(settings_data)
    assert settings.plugins.default == "plugin_1"

    with pytest.raises(ValidationError):
        invalid_data = {
            "plugins": {
                "default": "plugin_3",
                "enabled": ["plugin_1", "plugin_2"]
            }
        }
        CustomSettings.model_validate(invalid_data)
