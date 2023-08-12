from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from omnitool.plugin.configuration import (
    ContextResourceConfiguration,
    PluginConfiguration,
    _PluginConfigurationService,
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
def configuration_service(configuration_file):
    return _PluginConfigurationService(configuration_file, ContextResourceDataStub)


def test_load_configuration(configuration_service, configuration_model):
    configuration_service.load_configuration()

    expected_configuration_model = configuration_model.model_copy()
    for resource in expected_configuration_model.resources.values():
        resource.data = ContextResourceDataStub(resource.location.path)

    assert configuration_service._configuration == expected_configuration_model


def test_get_contexts(configuration_service):
    configuration_service.load_configuration()
    contexts = configuration_service.get_contexts()

    assert isinstance(contexts, dict)
    assert len(contexts) == 2
    assert "context1" in contexts
    assert "context2" in contexts


def test_add_resource(configuration_service):
    configuration_service.load_configuration()
    context_id = "context1"
    resource = ContextResourceConfiguration(
        name="New Resource",
        location=ContextResourceLocation(type="file", path="path/to/new_resource")
    )
    identifier = configuration_service.add_resource(context_id, resource)

    expected_data = ContextResourceDataStub(resource.location.path)
    expected_resource = resource.model_copy(update={"data": expected_data})

    assert len(configuration_service._configuration.resources) == 4
    assert len(configuration_service._configuration.contexts[context_id].resources) == 3
    assert configuration_service._configuration.resources[identifier] == expected_resource
