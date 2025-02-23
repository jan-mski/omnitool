from dataclasses import dataclass
from pathlib import Path

from omnitool_plugin_base.plugin.data import ContextResourceData, ContextResourceLocation


@dataclass
class ContextResourceDataStub(ContextResourceData):
    def __init__(self, path: Path):
        self.path = path

    @classmethod
    def load(cls, location: ContextResourceLocation) -> "ContextResourceData":
        return cls(location.path)
