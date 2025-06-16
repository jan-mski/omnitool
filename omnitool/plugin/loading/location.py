from abc import ABC, abstractmethod

from omnitool.plugin.api.definition import PluginDefinition


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
