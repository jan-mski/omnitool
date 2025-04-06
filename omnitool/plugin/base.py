from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from omnitool.plugin.configuration import PluginConfigurationService, ContextConfiguration, ContextResourceConfiguration
from omnitool_plugin_base.plugin.base import PluginDefinition


PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"


class PluginModule(ABC):
    loaded: bool = False

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def load(self) -> None:
        self.loaded = True


@dataclass
class PluginLocation:
    configuration_dir: Path
    plugin_module: PluginModule

    @property
    def configuration_file(self):
        return self.configuration_dir / PLUGIN_CONFIGURATION_FILE_NAME


class Plugin:
    definition: PluginDefinition
    location: PluginLocation
    _configuration_service: PluginConfigurationService

    def __init__(self,
                 configuration_service: PluginConfigurationService,
                 definition: PluginDefinition,
                 location: PluginLocation):
        self._configuration_service = configuration_service
        self.definition = definition
        self.location = location

    @property
    def name(self) -> str:
        return self.definition.name

    def get_contexts(self) -> Dict[str, ContextConfiguration]:
        return self._configuration_service.get_contexts()

    def add_resource(self, context_id: str, resource: ContextResourceConfiguration):
        self._configuration_service.add_resource(context_id, resource)
