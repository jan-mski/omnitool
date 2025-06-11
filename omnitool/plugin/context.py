from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


# TODO: update this class and replace in ResourceConfiguration with a URI string
# @dataclass
class Location(BaseModel):
    """
    Represents the location of a plugin context or resource.
    """
    # value: Path
    # type: str
    path: Path


@dataclass
class ResourceData(ABC):
    """
    Base class for all context resources.
    """


@dataclass
class Resource:
    """
    Represents a resource in a context.
    """
    name: str
    location: Location
    data: Optional[ResourceData] = None


@dataclass
class Context:
    """
    Represents a plugin context, which contains resources.
    """
    name: str
    resources: dict[str, Resource]
