import pytest

from omnitool_plugin_base.plugin.base import ContextResource


@pytest.fixture
def context_resource_type():
    class ContextResourceStub(ContextResource):
        pass

    return ContextResourceStub
