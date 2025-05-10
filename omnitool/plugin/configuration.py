import logging
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

from omnitool_plugin_base.plugin.configuration import ContextResourceConfiguration


logger = logging.getLogger(__name__)


class ContextConfiguration(BaseModel):
    name: str
    resources: Dict[str, ContextResourceConfiguration]


class PluginConfiguration(BaseModel):
    contexts: Optional[Dict[str, ContextConfiguration]] = Field(default_factory=dict)

    @property
    def resources(self) -> Dict[str, ContextResourceConfiguration]:
        resources = {}

        for context in self.contexts.values():
            resources.update(context.resources)

        return resources


class PluginConfigurationLoadError(Exception):
    def __init__(self, additional_info: str):
        super().__init__(f"Could not load plugin: {additional_info}")


def load_configuration(configuration_file: Path) -> PluginConfiguration:
    logger.debug(f"Reading configuration file '{configuration_file}'")

    if not configuration_file.exists():
        logger.debug("Configuration file not found, creating")
        configuration = PluginConfiguration()
        _save_configuration(configuration, configuration_file)
    elif not configuration_file.is_file():
        raise PluginConfigurationLoadError(f"Configuration file '{configuration_file}' is not a file")
    else:
        configuration_json = configuration_file.read_text(encoding="utf-8")
        configuration = PluginConfiguration.model_validate_json(configuration_json)
        logger.debug("Configuration file read successfully")

    return configuration


def _save_configuration(configuration: PluginConfiguration, configuration_file: Path) -> None:
    logger.debug(f"Saving configuration to file '{configuration_file}'")

    configuration_json = configuration.model_dump_json(indent=2)
    configuration_file.write_text(configuration_json, "utf-8")

    logger.debug("Configuration saved successfully")
