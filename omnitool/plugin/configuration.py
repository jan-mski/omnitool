import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type, Optional

from pydantic import BaseModel, Field

from omnitool_plugin_base.plugin.base import ContextResource
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


class PluginConfigurationService(ABC):
    @abstractmethod
    def load_configuration(self) -> PluginConfiguration:
        pass


class PluginConfigurationLoadError(Exception):
    def __init__(self, additional_info: str):
        super().__init__(f"Could not load plugin: {additional_info}")


class _PluginConfigurationService(PluginConfigurationService):
    _configuration_file: Path
    _configuration: PluginConfiguration
    _resource_type: Type[ContextResource]

    def __init__(self, configuration_file: Path, resource_type: Type[ContextResource]):
        self._configuration_file = configuration_file
        self._resource_type = resource_type

    def load_configuration(self) -> None:
        logger.debug(f"Reading configuration file '{self._configuration_file}'")

        if not self._configuration_file.exists():
            logger.debug("Configuration file not found, creating")
            self._configuration = PluginConfiguration()
            self._save_configuration()
        elif not self._configuration_file.is_file():
            raise PluginConfigurationLoadError(f"Configuration file '{self._configuration_file}' is not a file")
        else:
            configuration_json = self._configuration_file.read_text(encoding="utf-8")
            self._configuration = PluginConfiguration.model_validate_json(configuration_json)
            logger.debug("Configuration file read successfully")

    def _create_identifier(self) -> str:
        return str(uuid.uuid4())

    def _save_configuration(self) -> None:
        logger.debug(f"Saving configuration to file '{self._configuration_file}'")

        configuration_json = self._configuration.model_dump_json(indent=2)
        self._configuration_file.write_text(configuration_json, "utf-8")

        logger.debug("Configuration saved successfully")


def plugin_configuration_service(configuration_file: Path,
                                 resource_type: Type[ContextResource]) -> PluginConfigurationService:
    configuration_service = _PluginConfigurationService(configuration_file, resource_type)
    configuration_service.load_configuration()

    return configuration_service
