import pytest

from omnitool.plugin.operation import PluginOperationGroup


@pytest.fixture
def plugin_operation_group():
    """
    Fixture that returns a PluginOperationGroup instance for testing.
    """
    return PluginOperationGroup(name="test_group")


def test_plugin_operation_group(plugin_operation_group):
    """
    Test that PluginOperationGroup initializes with the correct name and empty lists.
    """
    assert plugin_operation_group.root_operation_name == "test_group"
    assert plugin_operation_group.subgroups == []
    assert plugin_operation_group.operations == []


def test_add_subgroup_adds_subgroup_to_list(plugin_operation_group):
    """
    Test that add_subgroup correctly adds a subgroup to the list.
    """
    subgroup = PluginOperationGroup(name="sub")
    plugin_operation_group.add_subgroup(subgroup)

    assert plugin_operation_group.subgroups == [subgroup]


def test_add_subgroup_raises_type_error_for_invalid_input(plugin_operation_group):
    """
    Test that add_subgroup raises a TypeError when input is not a PluginOperationGroup.
    """
    with pytest.raises(TypeError):
        plugin_operation_group.add_subgroup("not a group")


def test_operation_registers_both_decorator_styles_and_accumulates_functions(plugin_operation_group):
    """
    Test that the operation decorator registers functions in both decorator styles and accumulates them.
    """

    @plugin_operation_group.operation
    def op1(*args, **kwargs):
        return "first"

    @plugin_operation_group.operation()
    def op2(*args, **kwargs):
        return "second"

    assert plugin_operation_group.operations == [op1, op2]


def test_operation_registration_none_raises_error(plugin_operation_group):
    """
    Test that operation decorator raises ValueError if None is registered.
    """
    with pytest.raises(ValueError):
        plugin_operation_group.operation()(None)
