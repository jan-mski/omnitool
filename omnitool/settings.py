import abc
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


OMNITOOL_HOME_PATH = Path.home() / ".omnitool"
OMNITOOL_SETTINGS_FILE_PATH = OMNITOOL_HOME_PATH / "settings.json"
PLUGIN_CONFIGURATIONS_PATH = OMNITOOL_HOME_PATH / "plugins"
BUILTIN_PLUGIN_NAMES = ["git"]

logger = logging.getLogger(__name__)
omnitool_settings: Optional["OmnitoolSettings"] = None


class ConfiguredPlugins(BaseModel):
    enabled: list[str] = Field(frozen=True, min_length=1, default_factory=lambda: BUILTIN_PLUGIN_NAMES)
    default: Optional[str] = Field(frozen=True, default_factory=lambda data: data["enabled"][0])

    @model_validator(mode="after")
    def check_default_in_enabled(self):
        if self.default and self.default not in self.enabled:
            raise ValueError("Selected default plugin is not in the list of enabled plugins")

        return self


class OmnitoolSettings(BaseSettings, abc.ABC):
    model_config = SettingsConfigDict(json_file=OMNITOOL_SETTINGS_FILE_PATH)

    plugins: ConfiguredPlugins

    @property
    def enabled_builtin_plugins(self) -> list[str]:
        return [plugin for plugin in self.plugins.enabled if plugin in BUILTIN_PLUGIN_NAMES]

    @property
    def enabled_user_plugins(self):
        return [plugin for plugin in self.plugins.enabled if plugin not in BUILTIN_PLUGIN_NAMES]


class _OmnitoolSettings(OmnitoolSettings):
    pass


class OmnitoolSettingsLoadError(Exception):
    def __init__(self, additional_info: str):
        super().__init__(f"Error while loading Omnitool settings: {additional_info}")


def load_settings() -> OmnitoolSettings:
    global omnitool_settings

    logger.info("Loading Omnitool settings")

    if not OMNITOOL_SETTINGS_FILE_PATH.exists():
        logger.info("No Omnitool configuration file found, creating default")
        omnitool_settings = _load_default_settings()
    elif not OMNITOOL_SETTINGS_FILE_PATH.is_file():
        raise OmnitoolSettingsLoadError(f"Path '{OMNITOOL_SETTINGS_FILE_PATH}' does not point to a file")
    else:
        omnitool_settings = _load_settings()

    logger.info("Omnitool settings loaded successfully")
    logger.info(f"Enabled plugins: {omnitool_settings.plugins.enabled}")
    logger.info(f"Default plugin: {omnitool_settings.plugins.default}")

    return omnitool_settings


def _load_settings() -> _OmnitoolSettings:
    try:
        file_content = OMNITOOL_SETTINGS_FILE_PATH.read_text(encoding="utf-8")
        return _OmnitoolSettings.model_validate_json(file_content)
    except Exception as e:
        raise OmnitoolSettingsLoadError(str(e)) from e


def _load_default_settings() -> _OmnitoolSettings:
    default_settings = _OmnitoolSettings(plugins=ConfiguredPlugins())

    try:
        OMNITOOL_HOME_PATH.mkdir(parents=True, exist_ok=True)
        OMNITOOL_SETTINGS_FILE_PATH.write_text(default_settings.model_dump_json(), encoding="utf-8")
    except Exception as e:
        raise OmnitoolSettingsLoadError(str(e)) from e

    return default_settings
