from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse


@dataclass
class Location:
    """
    Represents the location of a plugin context or resource.
    """
    path: Path


@dataclass
class Resource:
    """
    Represents a resource in a context.
    """
    name: str
    location: Location
    data: Optional[Any] = None


@dataclass
class Context:
    """
    Represents a plugin context, which contains resources.
    """
    name: str
    resources: dict[str, Resource]


def parse_uri(uri: str) -> Location:
    """
    Factory function to create a Location object from a URI string.

    Args:
        uri: The URI string to parse. Must have a 'file://' prefix.

    Returns:
        Location: A Location object with the parsed path.

    Raises:
        ValueError: If the URI doesn't have a 'file://' prefix or is invalid.
    """
    parsed_uri = urlparse(uri)
    if parsed_uri.scheme != "file":
        raise ValueError(f"URI scheme must be 'file', got: {parsed_uri.scheme}")

    if not parsed_uri.path:
        raise ValueError(f"Invalid URI format: {uri}")

    return Location(path=Path(parsed_uri.path))
