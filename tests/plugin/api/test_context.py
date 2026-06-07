from pathlib import Path

import pytest

from omnitool.plugin.api.context import parse_uri, Location


def test_create_location_valid_file_uri():
    """
    Test that create_location correctly parses a valid file:// URI.
    """
    uri = "file:///path/to/resource"
    
    location = parse_uri(uri)
    
    assert isinstance(location, Location)
    assert location.path == Path("/path/to/resource")


def test_create_location_invalid_scheme():
    """
    Test that create_location raises ValueError for non-file:// schemes.
    """
    uri = "http://example.com/resource"
    
    with pytest.raises(ValueError):
        parse_uri(uri)


def test_create_location_missing_scheme():
    """
    Test that create_location raises ValueError for URIs without scheme.
    """
    uri = "path/to/resource"
    
    with pytest.raises(ValueError):
        parse_uri(uri)


def test_create_location_empty_uri():
    """
    Test that create_location raises ValueError for empty URI.
    """
    uri = ""
    
    with pytest.raises(ValueError):
        parse_uri(uri)


def test_create_location_empty_path():
    """
    Test that create_location raises ValueError for empty path.
    """
    uri = "file://"
    
    with pytest.raises(ValueError):
        parse_uri(uri)
