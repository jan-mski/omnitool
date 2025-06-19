import pytest

import omnitool.plugin.loading.loader as loader
import omnitool.cli.initialization as initialization
from omnitool.cli.initialization import callback, initialize_operations, app
from omnitool.plugin.loading.loader import LoadedPlugin


@pytest.fixture(autouse=True)
def reset_app():
    """
    Resets the global app state before each test to prevent test pollution.
    """
    app.registered_groups.clear()
    app.registered_commands.clear()
    yield


@pytest.fixture
def mock_loaded_plugins(mocker):
    """
    Mocks the loaded_plugins dictionary in the loader module.
    """

    def _mock_loaded_plugins(plugins: list[LoadedPlugin] = None):
        """
        Sets up the loaded_plugins mock to return the specified plugins.

        Args:
            plugins: List of LoadedPlugin instances.
                    Defaults to an empty list if None is provided.
        """
        if plugins is None:
            plugins = []

        plugins_dict = {plugin.name: plugin for plugin in plugins}
        mocker.patch.object(loader, "loaded_plugins", plugins_dict)

    return _mock_loaded_plugins


@pytest.fixture
def mock_cli_operation(mocker):
    """
    Mocks the cli_operation decorator function.
    """

    def _mock_cli_operation(plugin: LoadedPlugin, operation):
        return operation

    return mocker.patch.object(initialization, "cli_operation", side_effect=_mock_cli_operation)


def test_callback_executes_without_error():
    """
    Tests that the callback function executes successfully without raising exceptions.
    Expects function to complete execution without errors and return None.
    """
    result = callback()

    assert result is None


def test_initialize_operations_with_no_plugins(mock_loaded_plugins, mock_cli_operation):
    """
    Tests operation initialization when no plugins are loaded in the system.
    Expects function to complete without errors and make no modifications to the app.
    """
    mock_loaded_plugins([])

    initial_group_names = [group.name for group in app.registered_groups]

    initialize_operations()

    current_group_names = [group.name for group in app.registered_groups]

    assert current_group_names == initial_group_names

    mock_cli_operation.assert_not_called()


def test_initialize_operations_with_single_plugin(
    mocker, mock_loaded_plugins, create_loaded_plugin, mock_cli_operation
):
    """
    Tests operation initialization with one loaded plugin containing multiple operations.
    Expects plugin app creation, Typer subcommands to be created, and registration of all operations as decorated Typer commands.
    """
    plugin_name = "test_plugin"
    operation_names = ["start", "stop", "status"]

    plugin = create_loaded_plugin(plugin_name, operation_names=operation_names)
    mock_loaded_plugins([plugin])

    initialize_operations()

    expected_group_names = sorted([plugin_name])
    actual_group_names = sorted([group.name for group in app.registered_groups])

    expected_command_names = sorted(operation_names)
    actual_command_names = sorted(
        [command.name for command in app.registered_groups[0].typer_instance.registered_commands]
    )

    expected_calls = [mocker.call(plugin, operation) for operation in plugin.definition.operations]

    assert actual_group_names == expected_group_names
    assert actual_command_names == expected_command_names

    mock_cli_operation.assert_has_calls(expected_calls, any_order=True)


def test_initialize_operations_with_multiple_plugins(
    mocker, mock_loaded_plugins, create_loaded_plugin, mock_cli_operation
):
    """
    Tests operation initialization with multiple loaded plugins each containing operations.
    Expects separate plugin apps to be created for each plugin, Typer subcommands to be created, and all operations decorated as Typer commands.
    """
    plugin1_name = "plugin1"
    plugin2_name = "plugin2"
    plugin1_operation_names = ["init", "build"]
    plugin2_operation_names = ["deploy", "test", "clean"]

    plugin1 = create_loaded_plugin(plugin1_name, operation_names=plugin1_operation_names)
    plugin2 = create_loaded_plugin(plugin2_name, operation_names=plugin2_operation_names)

    mock_loaded_plugins([plugin1, plugin2])

    initialize_operations()

    expected_group_names = sorted([plugin1_name, plugin2_name])
    actual_group_names = sorted([group.name for group in app.registered_groups])

    expected_plugin1_command_names = sorted(plugin1_operation_names)
    actual_plugin1_command_names = sorted(
        [command.name for command in app.registered_groups[0].typer_instance.registered_commands]
    )

    expected_plugin2_command_names = sorted(plugin2_operation_names)
    actual_plugin2_command_names = sorted(
        [command.name for command in app.registered_groups[1].typer_instance.registered_commands]
    )

    expected_calls = [mocker.call(plugin1, operation) for operation in plugin1.definition.operations] + [
        mocker.call(plugin2, operation) for operation in plugin2.definition.operations
    ]

    assert actual_group_names == expected_group_names

    mock_cli_operation.assert_has_calls(expected_calls, any_order=True)
