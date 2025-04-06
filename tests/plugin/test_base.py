from pathlib import Path

import pytest
from omnitool.plugin.base import (Plugin, PluginConfigurationService, ContextConfiguration,
                                  ContextResourceConfiguration, PLUGIN_CONFIGURATION_FILE_NAME)
from omnitool.plugin.base import PluginLocation
from omnitool_plugin_base.plugin.data import ContextResourceLocation
from omnitool_plugin_base.plugin.base import PluginDefinition
from tests.plugin.utils import ContextResourceDataStub


@pytest.fixture
def plugin_config_service_mock(mocker):
    return mocker.MagicMock(spec=PluginConfigurationService)


@pytest.fixture
def plugin_definition():
    return PluginDefinition(name="test_plugin", resource_data_type=ContextResourceDataStub)


@pytest.fixture
def plugin_location(mocker):
    return PluginLocation(configuration_dir=Path("/root/dir/"),
                          plugin_module=mocker.MagicMock())


@pytest.fixture
def plugin(plugin_config_service_mock, plugin_definition, plugin_location):
    return Plugin(
        configuration_service=plugin_config_service_mock,
        definition=plugin_definition,
        location=plugin_location
    )


@pytest.fixture
def context_resource_configuration():
    return ContextResourceConfiguration(name="test_resource",
                                        location=ContextResourceLocation(path=Path("/root/dir/context/resource")))


@pytest.fixture
def context_configuration(context_resource_configuration):
    return ContextConfiguration(name="test_context",
                                resources={context_resource_configuration.name: context_resource_configuration})


def test_plugin_name(plugin, plugin_definition):
    assert plugin.name == plugin_definition.name


def test_plugin_get_contexts(plugin, plugin_config_service_mock, context_configuration):
    expected_contexts = {context_configuration.name: context_configuration}
    plugin_config_service_mock.get_contexts.return_value = expected_contexts

    assert plugin.get_contexts() == expected_contexts


def test_plugin_add_resource(plugin, plugin_config_service_mock, context_resource_configuration):
    plugin.add_resource(context_id="test_context", resource=context_resource_configuration)

    plugin_config_service_mock.add_resource.assert_called_once_with("test_context", context_resource_configuration)


def test_plugin_location_configuration_file(plugin_location):
    expected_file = plugin_location.configuration_dir / PLUGIN_CONFIGURATION_FILE_NAME

    assert plugin_location.configuration_file == expected_file
