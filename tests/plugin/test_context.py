from omnitool.plugin.context import ResourceData


def test_resource_data_subclass():
    """
    Test that a subclass of ResourceData is an instance of ResourceData.
    """

    class ResourceDataStub(ResourceData):
        pass

    stub = ResourceDataStub()

    assert isinstance(stub, ResourceData)
