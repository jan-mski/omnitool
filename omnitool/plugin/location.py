from abc import ABC, abstractmethod
from dataclasses import dataclass

from omnitool.plugin.definition import PluginDefinition


class PluginModule(ABC):
    """
    Abstract base class for plugin modules.
    """

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
        pass


@dataclass
class PluginLocation:
    """
    Represents the location of a plugin.
    """
    plugin_module: PluginModule

    @property
    def plugin_name(self) -> str:
        return self.plugin_module.name

    def load_module(self) -> PluginDefinition:
        return self.plugin_module.load()
