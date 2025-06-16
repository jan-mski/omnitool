import pytest
from omnitool.plugin.loading.location import PluginModule
from omnitool.plugin.api.definition import PluginDefinition


def test_plugin_module_cannot_be_instantiated_directly():
    """
    Tests that the abstract base class PluginModule cannot be instantiated directly.
    Expects TypeError to be raised when attempting to create an instance.
    """
    with pytest.raises(TypeError):
        PluginModule()


def test_plugin_module_concrete_implementation(mocker):
    """
    Tests that a concrete implementation of PluginModule can be created when all
    abstract methods are implemented.
    Expects the concrete implementation to be instantiable without errors.
    """

    class PluginModuleStub(PluginModule):
        @property
        def source(self) -> str:
            return "stub_source"

        @property
        def name(self) -> str:
            return "stub_name"

        def load(self) -> PluginDefinition:
            return mocker.Mock(spec=PluginDefinition)

    plugin_module = PluginModuleStub()

    assert isinstance(plugin_module, PluginModule)
    assert plugin_module.source == "stub_source"
    assert plugin_module.name == "stub_name"
    assert isinstance(plugin_module.load(), PluginDefinition)


def test_plugin_module_requires_source_implementation(mocker):
    """
    Tests that a concrete implementation must provide a source property.
    Expects TypeError to be raised when the source property is not implemented.
    """

    class PluginModuleNoSource(PluginModule):
        @property
        def name(self) -> str:
            return "stub_name"

        def load(self) -> PluginDefinition:
            return mocker.Mock(spec=PluginDefinition)

    with pytest.raises(TypeError):
        PluginModuleNoSource()


def test_plugin_module_requires_name_implementation(mocker):
    """
    Tests that a concrete implementation must provide a name property.
    Expects TypeError to be raised when the name property is not implemented.
    """

    class PluginModuleNoName(PluginModule):
        @property
        def source(self) -> str:
            return "stub_source"

        def load(self) -> PluginDefinition:
            return mocker.Mock(spec=PluginDefinition)

    with pytest.raises(TypeError):
        PluginModuleNoName()


def test_plugin_module_requires_load_implementation():
    """
    Tests that a concrete implementation must provide a load method.
    Expects TypeError to be raised when the load method is not implemented.
    """

    class PluginModuleNoLoad(PluginModule):
        @property
        def source(self) -> str:
            return "stub_source"

        @property
        def name(self) -> str:
            return "stub_name"

    with pytest.raises(TypeError):
        PluginModuleNoLoad()
