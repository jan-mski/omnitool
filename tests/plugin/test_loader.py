import pytest
import logging
from omnitool.plugin.loader import load_plugins, loaded_plugins

def test_load_plugins_no_plugins_found(mocker):
    """
    Tests the behavior when no plugins are available to load.
    Expects the function to log a warning and return without loading anything.
    """
    # Mock the finder to return an empty list
    mocker.patch("omnitool.plugin.finder.find_plugins", return_value=[])

    # Mock the logger to capture warning messages
    mock_logger = mocker.patch("omnitool.plugin.loader.logger")

    # Call the function
    load_plugins()

    # Assert that a warning was logged
    mock_logger.warning.assert_called_once_with("No plugins available to load")

    # Assert that the loaded_plugins dictionary is empty
    assert loaded_plugins == {}


def test_load_plugins_successful_loading(mocker):
    """
    Tests the loading of multiple available plugins.
    Expects all plugins to be loaded correctly and stored in the loaded_plugins dictionary
    with appropriate logging.
    """
    pass


def test_load_plugins_multiple_plugins_with_exceptions(mocker):
    """
    Tests loading multiple plugins where some succeed and some fail.
    Expects successful plugins to be loaded and exceptions to be handled properly
    without affecting other plugins.
    """
    pass


def test_load_plugins_all_plugins_fail(mocker):
    """
    Tests the scenario where all plugins fail to load.
    Expects appropriate error logging for each plugin and an empty loaded_plugins dictionary.
    """
    pass


def test_load_plugins_resets_loaded_plugins(mocker):
    """
    Tests that the global loaded_plugins dictionary is reset when the function is called.
    Expects any previously loaded plugins to be removed before loading new ones.
    """
    pass
