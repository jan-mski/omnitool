import json
import logging
from pathlib import Path
from typing import Dict, Type

from pydantic import BaseModel, ConfigDict

from omnitooldef.plugin.data import ContextResourceData, ContextResourceLocation


logger = logging.getLogger(__name__)


class ContextResourceConfiguration(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    location: ContextResourceLocation
    data: ContextResourceData = None


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


class PluginConfigurationService:
    _configuration_file: Path
    _configuration: PluginConfiguration
    _resource_data_type: Type[ContextResourceData]

    def __init__(self, configuration_file: Path, resource_data_type: Type[ContextResourceData]):
        self._configuration_file = configuration_file
        self._resource_data_type = resource_data_type

    def get_contexts(self) -> Dict[str, ContextConfiguration]:
        return self._configuration.contexts

    def load_configuration(self):  # TODO: factory method would be better
        logger.info("Reading configuration file '%s'", self._configuration_file)

        self._load_configuration()
        self._load_data()

    def _load_configuration(self):
        configuration_text = self._configuration_file.read_text("utf-8")
        configuration_json = json.loads(configuration_text)
        self._configuration = PluginConfiguration.model_validate(configuration_json)

    def _load_data(self):
        for resource in self._configuration.resources.values():
            resource.data = self._resource_data_type.load(resource.location)
