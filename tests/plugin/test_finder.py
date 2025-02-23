from pathlib import Path

import pytest

from omnitool.plugin import finder
from omnitool.plugin.finder import PluginLocation


RELATIVE_BUILTIN_PLUGINS_DIR = "plugin/builtin"
RELATIVE_USER_PLUGINS_DIR = ".omnitool/plugins"
PLUGIN_MODULE_FILE_NAME = "plugin.py"
PLUGIN_CONFIGURATION_FILE_NAME = "configuration.json"


@pytest.fixture()
def app_root_dir(tmp_path):
    return tmp_path


@pytest.fixture
def user_home_dir(tmp_path, mocker):
    mocker.patch.object(Path, "home", return_value=tmp_path)

    return tmp_path


@pytest.fixture
def builtin_plugins_dir(app_root_dir):
    user_plugins_dir = app_root_dir / "plugin" / "builtin"
    user_plugins_dir.mkdir(parents=True)

    return user_plugins_dir


@pytest.fixture
def user_plugins_dir(user_home_dir):
    user_plugins_dir = user_home_dir / RELATIVE_USER_PLUGINS_DIR
    user_plugins_dir.mkdir(parents=True)

    return user_plugins_dir


@pytest.fixture
def plugin_dir(app_root_dir, builtin_plugins_dir, user_plugins_dir):
    def _plugin_dir(name: str, user: bool, module: bool, configuration: bool):
        if user:
            plugin_dir = user_plugins_dir / name
        else:
            plugin_dir = builtin_plugins_dir / name

        plugin_dir.mkdir(parents=True)

        if module:
            (plugin_dir / PLUGIN_MODULE_FILE_NAME).touch()

        if configuration:
            (plugin_dir / PLUGIN_CONFIGURATION_FILE_NAME).touch()

        return plugin_dir

    return _plugin_dir


def test_find_plugins(app_root_dir, plugin_dir):
    valid_user_plugin_dir = plugin_dir("valid_user_plugin", user=True, module=True, configuration=True)
    valid_builtin_plugin_dir = plugin_dir("valid_builtin_plugin", user=False, module=True, configuration=True)

    actual_plugin_locations = finder.find_plugins(app_root_dir)

    expected_plugin_locations = [
        PluginLocation(
            root_dir=valid_builtin_plugin_dir,
            module_file=valid_builtin_plugin_dir / PLUGIN_MODULE_FILE_NAME,
            configuration_file=valid_builtin_plugin_dir / PLUGIN_CONFIGURATION_FILE_NAME
        ),
        PluginLocation(
            root_dir=valid_user_plugin_dir,
            module_file=valid_user_plugin_dir / PLUGIN_MODULE_FILE_NAME,
            configuration_file=valid_user_plugin_dir / PLUGIN_CONFIGURATION_FILE_NAME
        )
    ]

    assert actual_plugin_locations == expected_plugin_locations


def test_find_plugins_invalid_plugin_dirs(app_root_dir, plugin_dir, user_plugins_dir):
    plugin_dir("plugin_dir_missing_module_file", user=True, module=False, configuration=True)
    plugin_dir("plugin_dir_missing_configuration_file", user=True, module=True, configuration=False)

    plugin_dir_not_a_dir = user_plugins_dir / "plugin_dir_not_a_dir"
    plugin_dir_not_a_dir.touch()

    actual_plugin_locations = finder.find_plugins(app_root_dir)

    assert actual_plugin_locations == []


def test_find_plugins_no_plugin_dir(app_root_dir, user_home_dir, plugin_dir):
    plugin_dir = user_home_dir / RELATIVE_USER_PLUGINS_DIR

    actual_plugin_locations = finder.find_plugins(app_root_dir)

    assert plugin_dir.is_dir()
    assert actual_plugin_locations == []
