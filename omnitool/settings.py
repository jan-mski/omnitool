import abc
import logging
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


OMNITOOL_HOME_PATH = Path.home() / ".omnitool"
OMNITOOL_SETTINGS_FILE_PATH = OMNITOOL_HOME_PATH / "settings.json"
DEFAULT_ENABLED_PLUGIN_NAMES = ["git"]

logger = logging.getLogger(__name__)
omnitool_settings: Optional["OmnitoolSettings"] = None


class ConfiguredPlugins(BaseModel):
    default: Optional[str] = Field(frozen=True, default=None)
    enabled: List[str] = Field(frozen=True, min_length=1, default=None)

    @model_validator(mode="after")
    def check_default_in_enabled(self):
        if self.default and self.default not in self.enabled:
            raise ValueError("Selected default plugin is not in the list of enabled plugins")

        return self


class OmnitoolSettings(BaseSettings, abc.ABC):
    model_config = SettingsConfigDict(json_file=OMNITOOL_SETTINGS_FILE_PATH)

    plugins: ConfiguredPlugins


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
        _create_default_configuration()
    elif not OMNITOOL_SETTINGS_FILE_PATH.is_file():
        raise OmnitoolSettingsLoadError(f"Path '{OMNITOOL_SETTINGS_FILE_PATH}' does not point to a file")

    try:
        file_content = OMNITOOL_SETTINGS_FILE_PATH.read_text(encoding="utf-8")
        omnitool_settings = _OmnitoolSettings.model_validate_json(file_content)
    except Exception as e:
        raise OmnitoolSettingsLoadError(str(e)) from e

    logger.info("Omnitool settings loaded successfully")
    logger.info(f"Enabled plugins: {omnitool_settings.plugins.enabled}")
    logger.info(f"Default plugin: {omnitool_settings.plugins.default}")

    return omnitool_settings


def _create_default_configuration():
    OMNITOOL_HOME_PATH.mkdir(parents=True, exist_ok=True)

    default_settings = _OmnitoolSettings(plugins=ConfiguredPlugins(
        enabled=DEFAULT_ENABLED_PLUGIN_NAMES,
        default=DEFAULT_ENABLED_PLUGIN_NAMES[0]))

    OMNITOOL_SETTINGS_FILE_PATH.write_text(default_settings.model_dump_json(), encoding="utf-8")
