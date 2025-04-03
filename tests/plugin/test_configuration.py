import json
from pathlib import Path

import pytest

from omnitool.plugin.configuration import (
    ContextResourceConfiguration,
    PluginConfiguration,
    _PluginConfigurationService,
    plugin_configuration_service,
)
from omnitool_plugin_base.plugin.data import ContextResourceLocation
from tests.plugin.utils import ContextResourceDataStub


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
                            "path": "path/to/resource1",
                        },
                    },
                    "resource2": {
                        "name": "Resource 2",
                        "location": {
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
                            "path": "path/to/resource3",
                        },
                    },
                },
            },
        },
    }


@pytest.fixture
def create_configuration_file(tmp_path, configuration_json):
    def _create_configuration_file(write: bool = True):
        configuration_file = tmp_path / "test_configuration.json"

        if write:
            configuration_file.write_text(json.dumps(configuration_json))

        return configuration_file

    return _create_configuration_file


@pytest.fixture
def configuration_service(create_configuration_file):
    return _PluginConfigurationService(configuration_file=create_configuration_file(),
                                       resource_data_type=ContextResourceDataStub)


@pytest.fixture
def loaded_configuration_model(configuration_json):
    loaded_configuration_model = PluginConfiguration.model_validate(configuration_json)

    for resource in loaded_configuration_model.resources.values():
        resource.data = ContextResourceDataStub(resource.location.path)

    return loaded_configuration_model


class TestPluginConfiguration:
    def test_empty(self):
        empty_configuration = PluginConfiguration()

        assert empty_configuration.contexts == {}
        assert empty_configuration.resources == {}

    def test_resources(self, configuration_json):
        configuration_model = PluginConfiguration.model_validate(configuration_json)

        expected_paths = json.loads(json.dumps(configuration_json))  # Deep copy
        for context in expected_paths["contexts"].values():
            for resource in context["resources"].values():
                resource["location"]["path"] = Path(resource["location"]["path"])

        assert configuration_model.model_dump() == expected_paths


class TestPluginConfigurationService:
    def test_load_configuration(self, configuration_service, loaded_configuration_model):
        configuration_service.load_configuration()

        assert configuration_service._configuration == loaded_configuration_model

    def test_load_configuration_nonexistent_file(self, create_configuration_file):
        configuration_file = create_configuration_file(write=False)
        configuration_service = _PluginConfigurationService(configuration_file=configuration_file,
                                                            resource_data_type=ContextResourceDataStub)
        expected_file_content = PluginConfiguration().model_dump_json(indent=2)

        configuration_service.load_configuration()

        assert configuration_service.get_contexts() == {}
        assert configuration_file.is_file()
        assert configuration_file.read_text(encoding="utf-8") == expected_file_content

    def test_get_contexts(self, configuration_service, loaded_configuration_model):
        configuration_service.load_configuration()

        contexts = configuration_service.get_contexts()

        assert len(contexts) == len(loaded_configuration_model.contexts)

        for context_id, context in contexts.items():
            assert context_id in loaded_configuration_model.contexts
            assert context == loaded_configuration_model.contexts[context_id]

    def test_add_resource(self, configuration_service, create_configuration_file, loaded_configuration_model):
        configuration_service.load_configuration()

        context_id = list(loaded_configuration_model.contexts.keys())[0]
        resource = ContextResourceConfiguration(
            name="New Resource",
            location=ContextResourceLocation(path=Path("path/to/new_resource"))
        )
        resource_id = configuration_service.add_resource(context_id, resource)

        expected_resource = resource.model_copy(update={"data": ContextResourceDataStub(resource.location.path)})
        expected_configuration_model = loaded_configuration_model.model_copy(deep=True)
        expected_configuration_model.contexts[context_id].resources[resource_id] = expected_resource
        expected_file_content = expected_configuration_model.model_dump_json(indent=2)

        assert len(configuration_service._configuration.resources) == 4
        assert len(configuration_service._configuration.contexts[context_id].resources) == 3
        assert configuration_service._configuration.resources[resource_id] == expected_resource
        assert configuration_service._configuration_file.read_text("utf-8") == expected_file_content


def test_plugin_configuration_service(configuration_service, create_configuration_file):
    configuration_service.load_configuration()

    actual_configuration_service = plugin_configuration_service(configuration_file=create_configuration_file(),
                                                                resource_data_type=ContextResourceDataStub)

    assert isinstance(actual_configuration_service, _PluginConfigurationService)
    assert actual_configuration_service._configuration_file == configuration_service._configuration_file
    assert actual_configuration_service._resource_data_type == configuration_service._resource_data_type
    assert actual_configuration_service._configuration == configuration_service._configuration
