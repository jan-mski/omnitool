from omnitool.plugin.api.definition import PluginDefinition


def test_plugin_definition(create_plugin_definition, resource_data_type):
    """
    Tests the initialization of the PluginDefinition class.
    Expects the fields to be set correctly.
    """
    plugin_name = "test_plugin"
    plugin_definition = create_plugin_definition(plugin_name)

    assert plugin_definition.root_operation_name == "test_plugin"
    assert plugin_definition.operations == []
    assert plugin_definition.resource_data_type == resource_data_type


def test_plugin_definition_add_operation(create_plugin_definition):
    """
    Tests the addition of a resource operation to the PluginDefinition class.
    Expects the operation to be added to the operation registry.
    """
    plugin_name = "test_plugin"
    plugin_definition = create_plugin_definition(plugin_name)

    @plugin_definition.operation
    def test_operation():
        pass

    expected_plugin_operations = [test_operation]

    assert plugin_definition.operations == expected_plugin_operations
