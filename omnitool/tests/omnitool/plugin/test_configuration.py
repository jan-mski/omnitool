from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from omnitool.plugin.configuration import (
    ContextResourceConfiguration,
    PluginConfiguration,
    _PluginConfigurationService,
    plugin_configuration_service,
)
from omnitool_base.plugin.data import ContextResourceData, ContextResourceLocation


@dataclass
class ContextResourceDataStub(ContextResourceData):
    def __init__(self, path: Path):
        self.path = path

    @classmethod
    def load(cls, location: ContextResourceLocation) -> "ContextResourceData":
        return cls(location.path)


@pytest.fixture
def configuration_json():
    return {
        "contexts": {
            "context1": {
                "name": "Context 1",
                "resources": {
                    "resource1": {
                        "name": "Resource 1",
                        "location": {
                            "type": "file",
                            "path": "path/to/resource1",
                        },
                    },
                    "resource2": {
                        "name": "Resource 2",
                        "location": {
                            "type": "file",
                            "path": "path/to/resource2",
                        },
                    },
                },
            },
            "context2": {
                "name": "Context 2",
                "resources": {
                    "resource3": {
                        "name": "Resource 3",
                        "location": {
                            "type": "file",
                            "path": "path/to/resource3",
                        },
                    },
                },
            },
        },
    }


@pytest.fixture
def configuration_file(tmp_path, configuration_json):
    configuration_file = tmp_path / "test_configuration.json"
    configuration_file.write_text(json.dumps(configuration_json))

    return configuration_file


@pytest.fixture
def configuration_model(configuration_json):
    return PluginConfiguration.model_validate(configuration_json)


@pytest.fixture
def loaded_configuration_model(configuration_model):
    loaded_configuration_model = configuration_model.model_copy(deep=True)

    for resource in loaded_configuration_model.resources.values():
        resource.data = ContextResourceDataStub(resource.location.path)

    return loaded_configuration_model


@pytest.fixture
def configuration_service(configuration_file):
    return _PluginConfigurationService(configuration_file, ContextResourceDataStub)


class TestPluginConfiguration:
    def test_resources(self, configuration_model):
        assert len(configuration_model.resources) == 3

        for _, context in configuration_model.contexts.items():
            for resource_id, resource in context.resources.items():
                assert resource_id in configuration_model.resources
                assert resource == configuration_model.resources[resource_id]


class TestPluginConfigurationService:
    def test_load_configuration(self, configuration_service, loaded_configuration_model):
        configuration_service.load_configuration()

        assert configuration_service._configuration == loaded_configuration_model

    def test_get_contexts(self, configuration_service, loaded_configuration_model):
        configuration_service.load_configuration()

        contexts = configuration_service.get_contexts()

        assert len(contexts) == len(loaded_configuration_model.contexts)

        for context_id, context in contexts.items():
            assert context_id in loaded_configuration_model.contexts
            assert context == loaded_configuration_model.contexts[context_id]

    def test_add_resource(self, configuration_service, configuration_file, loaded_configuration_model):
        configuration_service.load_configuration()

        context_id = list(loaded_configuration_model.contexts.keys())[0]
        resource = ContextResourceConfiguration(
            name="New Resource",
            location=ContextResourceLocation(type="file", path="path/to/new_resource")
        )
        resource_id = configuration_service.add_resource(context_id, resource)

        expected_resource = resource.model_copy(update={"data": ContextResourceDataStub(resource.location.path)})
        expected_configuration_model = loaded_configuration_model.model_copy(deep=True)
        expected_configuration_model.contexts[context_id].resources[resource_id] = expected_resource

        assert len(configuration_service._configuration.resources) == 4
        assert len(configuration_service._configuration.contexts[context_id].resources) == 3
        assert configuration_service._configuration.resources[resource_id] == expected_resource
        assert configuration_file.read_text("utf-8") == expected_configuration_model.model_dump_json(indent=4)


def test_plugin_configuration_service(configuration_service, configuration_file):
    configuration_service.load_configuration()

    actual_configuration_service = plugin_configuration_service(configuration_file, ContextResourceDataStub)

    assert isinstance(actual_configuration_service, _PluginConfigurationService)
    assert actual_configuration_service._configuration_file == configuration_service._configuration_file
    assert actual_configuration_service._resource_data_type == configuration_service._resource_data_type
    assert actual_configuration_service._configuration == configuration_service._configuration
