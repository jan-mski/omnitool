from abc import ABC, abstractmethod
from dataclasses import dataclass

from omnitool.plugin.configuration import PluginConfiguration
from omnitool_plugin_base.plugin.base import PluginDefinition


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
    plugin_module: PluginModule

    @property
    def plugin_name(self) -> str:
        return self.plugin_module.name

    def load_module(self) -> PluginDefinition:
        return self.plugin_module.load()


@dataclass
class Plugin:
    configuration: PluginConfiguration
    definition: PluginDefinition
    location: PluginLocation

    @property
    def name(self) -> str:
        return self.location.plugin_name
