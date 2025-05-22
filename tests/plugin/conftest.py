import json
import pytest

from omnitool_plugin_base.plugin.base import ContextResource
from omnitool.plugin.configuration import PluginConfiguration


@pytest.fixture
def context_resource_type():
    class ContextResourceStub(ContextResource):
        pass

    return ContextResourceStub


@pytest.fixture
def configuration_json():
    """
    Provides a test configuration in JSON format with sample contexts and resources.

    Returns:
        str: A JSON string representing plugin configuration with contexts and resources
    """
    return json.dumps({
        "contexts": [
            {
                "name": "Context 1",
                "resources": [
                    {
                        "name": "Resource 1",
                        "location": {
                            "path": "path/to/resource1"
                        }
                    },
                    {
                        "name": "Resource 2",
                        "location": {
                            "path": "path/to/resource2"
                        }
                    }
                ]
            },
            {
                "name": "Context 2",
                "resources": {}
            }
        ]
    })


@pytest.fixture
def configuration_model(configuration_json):
    """
    Creates a validated PluginConfiguration model with test data.

    Args:
        configuration_json: The test configuration data

    Returns:
        PluginConfiguration: A validated configuration model with populated resource data
    """
    return PluginConfiguration.model_validate_json(configuration_json)
