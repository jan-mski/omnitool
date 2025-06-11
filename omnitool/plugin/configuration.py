import logging
from pathlib import Path
from typing import Optional, Annotated

from pydantic import BaseModel, Field, BeforeValidator, ConfigDict

from omnitool import settings
from omnitool.plugin.context import Location


PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"

logger = logging.getLogger(__name__)

plugin_configurations: dict[str, "PluginConfiguration"] = {}


def _named_configurations_list_to_dict(value: list):
    return {configuration["name"]: configuration for configuration in value} if value else {}


ContextsDictType = Annotated[
    dict[str, "ContextConfiguration"],
    BeforeValidator(_named_configurations_list_to_dict)
]
ResourcesDictType = Annotated[
    dict[str, "ResourceConfiguration"],
    BeforeValidator(_named_configurations_list_to_dict)
]


class ResourceConfiguration(BaseModel):
    """
    Configuration for context resources, including a name and location.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    location: Location


class ContextConfiguration(BaseModel):
    """
    Configuration for a plugin context, including a name and resources.
    """
    name: str
    resources: Optional[ResourcesDictType] = Field(default_factory=dict)


class PluginConfiguration(BaseModel):
    """
    Configuration for a plugin, including contexts and their resources.
    """
    contexts: Optional[ContextsDictType] = Field(default_factory=dict)


class PluginConfigurationLoadError(Exception):
    """
    Exception raised when a plugin configuration cannot be loaded.
    """

    def __init__(self, additional_info: str):
        super().__init__(f"Could not load plugin configuration: {additional_info}")


def load_configuration(plugin_name: str) -> PluginConfiguration:
    """
    Load the configuration for a plugin.

    Args:
        plugin_name: The name of the plugin

    Returns:
        PluginConfiguration: The loaded configuration

    Raises:
        PluginConfigurationLoadError: If the configuration file is not a file
    """
    try:
        configuration_file = _get_configuration_file_path(plugin_name)
    except Exception as e:
        raise PluginConfigurationLoadError(str(e)) from e

    logger.debug(f"Reading configuration file '{configuration_file}'")

    if configuration_file.exists():
        configuration_json = configuration_file.read_text(encoding="utf-8")
        configuration = PluginConfiguration.model_validate_json(configuration_json)
        logger.debug("Configuration file read successfully")
    else:
        logger.debug("Configuration file not found, creating")
        configuration = PluginConfiguration()
        _save_configuration(configuration, configuration_file)

    return configuration


def _get_configuration_file_path(plugin_name: str) -> Path:
    configuration_dir = _find_plugin_configuration_dir(plugin_name)
    _validate_configuration_dir(configuration_dir)

    configuration_file_path = configuration_dir / PLUGIN_CONFIGURATION_FILE_NAME
    _validate_configuration_file_path(configuration_file_path)

    return configuration_file_path


def _save_configuration(configuration: PluginConfiguration, configuration_file: Path) -> None:
    logger.debug(f"Saving configuration to file '{configuration_file}'")

    configuration_json = configuration.model_dump_json(indent=2)
    configuration_file.write_text(configuration_json, "utf-8")

    logger.debug("Configuration saved successfully")


def _find_plugin_configuration_dir(plugin_name: str) -> Path:
    configuration_dir = settings.PLUGIN_CONFIGURATIONS_PATH / plugin_name

    if not configuration_dir.exists():
        configuration_dir.mkdir(parents=True)

    logger.debug(f"LoadedPlugin configuration directory for '{plugin_name}' is '{configuration_dir}'")

    return configuration_dir


def _validate_configuration_dir(configuration_dir: Path) -> None:
    if configuration_dir.exists() and not configuration_dir.is_dir():
        raise ValueError(f"LoadedPlugin configuration directory '{configuration_dir}' is not a directory")


def _validate_configuration_file_path(configuration_file_path: Path) -> None:
    if configuration_file_path.exists() and not configuration_file_path.is_file():
        raise ValueError(f"LoadedPlugin configuration file '{configuration_file_path}' is not a file")
