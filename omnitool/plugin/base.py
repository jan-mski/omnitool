from abc import ABC, abstractmethod
from dataclasses import dataclass, field, InitVar
from pathlib import Path
from typing import Dict

from omnitool.plugin.configuration import PluginConfigurationService, ContextConfiguration, ContextResourceConfiguration
from omnitool_plugin_base.plugin.base import PluginDefinition


PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"


class PluginModule(ABC):
    loaded: bool = False

    @property
    @abstractmethod
    def source(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def load(self) -> PluginDefinition:
        self.loaded = True


@dataclass
class PluginLocation:
    configuration_dir: Path
    plugin_module: PluginModule

    @property
    def plugin_name(self) -> str:
        return self.plugin_module.name

    @property
    def configuration_file(self):
        return self.configuration_dir / PLUGIN_CONFIGURATION_FILE_NAME

    def load_module(self) -> PluginDefinition:
        return self.plugin_module.load()


@dataclass
class Plugin:
    _configuration_service: PluginConfigurationService = field(init=False, repr=False)
    configuration_service: InitVar[PluginConfigurationService]
    definition: PluginDefinition
    location: PluginLocation

    def __post_init__(self, configuration_service: PluginConfigurationService):
        self._configuration_service = configuration_service

    @property
    def name(self) -> str:
        return self.definition.name

    def get_contexts(self) -> Dict[str, ContextConfiguration]:
        return self._configuration_service.get_contexts()

    def add_resource(self, context_id: str, resource: ContextResourceConfiguration):
        self._configuration_service.add_resource(context_id, resource)
