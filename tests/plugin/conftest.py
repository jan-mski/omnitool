import json

import pytest

from omnitool.plugin.loading.configuration import PluginConfiguration
from omnitool.plugin.api.context import ResourceData


@pytest.fixture
def resource_data_type():
    class ResourceDataStub(ResourceData):
        pass

    return ResourceDataStub


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
                        "uri": "file:///path/to/resource1"
                    },
                    {
                        "name": "Resource 2",
                        "uri": "file:///path/to/resource2"
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
    return PluginConfiguration(contexts=[
        {
            "name": "Context 1",
            "resources": [
                {
                    "name": "Resource 1",
                    "uri": "file:///path/to/resource1"
                },
                {
                    "name": "Resource 2",
                    "uri": "file:///path/to/resource2"
                }
            ]
        },
        {
            "name": "Context 2",
            "resources": {}
        }
    ]
    )
