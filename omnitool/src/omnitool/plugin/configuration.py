import json
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type

from pydantic import BaseModel, ConfigDict, Field

from omnitool_base.plugin.data import ContextResourceData, ContextResourceLocation


logger = logging.getLogger(__name__)


class ContextResourceConfiguration(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    location: ContextResourceLocation
    data: ContextResourceData = Field(default=None, init_var=False, exclude=True)


class ContextConfiguration(BaseModel):
    name: str
    resources: Dict[str, ContextResourceConfiguration]


class PluginConfiguration(BaseModel):
    contexts: Dict[str, ContextConfiguration]

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

    @abstractmethod
    def get_contexts(self) -> Dict[str, ContextConfiguration]:
        pass

    @abstractmethod
    def add_resource(self, context_id: str, resource: ContextResourceConfiguration):
        pass


class _PluginConfigurationService(PluginConfigurationService):
    _configuration_file: Path
    _configuration: PluginConfiguration
    _resource_data_type: Type[ContextResourceData]

    def __init__(self, configuration_file: Path, resource_data_type: Type[ContextResourceData]):
        self._configuration_file = configuration_file
        self._resource_data_type = resource_data_type

    def load_configuration(self) -> None:
        configuration_json = self._read_configuration_file()
        self._load_configuration(configuration_json)
        self._load_data()

    def get_contexts(self) -> Dict[str, ContextConfiguration]:
        return self._configuration.contexts

    def add_resource(self, context_id: str, resource: ContextResourceConfiguration) -> str:
        identifier = self._create_identifier()
        resource.data = self._load_resource_data(resource)
        self._configuration.contexts[context_id].resources[identifier] = resource
        self._save_configuration()

        return identifier

    def _read_configuration_file(self):
        logger.info("Reading configuration file '%s'", self._configuration_file)

        configuration_text = self._configuration_file.read_text("utf-8")
        configuration_json = json.loads(configuration_text)

        logger.info("Configuration file read successfully.")

        return configuration_json

    def _load_configuration(self, configuration_json: dict):
        logger.info("Validating configuration from file '%s'", self._configuration_file)

        self._configuration = PluginConfiguration.model_validate(configuration_json)

        logger.info("Configuration validated successfully.")

    def _load_data(self):
        logger.info("Loading data from configuration file '%s'", self._configuration_file)

        for resource in self._configuration.resources.values():
            resource.data = self._load_resource_data(resource)

        logger.info("Data loaded successfully.", self._configuration_file)

    def _load_resource_data(self, resource: ContextResourceConfiguration):
        return self._resource_data_type.load(resource.location)

    def _create_identifier(self):
        return str(uuid.uuid4())

    def _save_configuration(self):
        logger.info("Saving configuration to file '%s'", self._configuration_file)

        configuration_json = self._configuration.model_dump_json(indent=4)
        self._configuration_file.write_text(configuration_json, "utf-8")

        logger.info("Configuration saved successfully.", self._configuration_file)


def plugin_configuration_service(configuration_file: Path,
                                 resource_data_type: Type[ContextResourceData]) -> PluginConfigurationService:
    configuration_service = _PluginConfigurationService(configuration_file, resource_data_type)
    configuration_service.load_configuration()

    return configuration_service
