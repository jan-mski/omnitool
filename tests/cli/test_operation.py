from pathlib import Path
from typing import Any, cast

import pytest
import click

import omnitool.cli.operation as operation
from omnitool.cli.operation import cli_operation, OperationExecutionError
from omnitool.plugin.api.context import Context, Resource, Location
from omnitool.plugin.api.operation import OperationFunction


@pytest.fixture
def sample_context():
    """
    Provides a sample context with resources for testing.
    """
    resources = {
        "resource1": Resource(name="resource1", location=Location(path=Path("/test/resource1")), data=None),
        "resource2": Resource(name="resource2", location=Location(path=Path("/test/resource2")), data=None),
    }
    return Context(name="test_context", resources=resources)


@pytest.fixture
def empty_context():
    """
    Provides an empty context with no resources for testing.
    """
    return Context(name="empty_context", resources={})


@pytest.fixture
def sample_operation() -> OperationFunction:
    """
    Provides a sample operation function for testing.
    """

    def test_operation(*args: Any, context: Context, **kwargs: Any) -> Any:
        """Test operation docstring."""

        return {
            "args": args,
            "kwargs": kwargs,
            "context_name": context.name if context else None,
            "resource_names": list(context.resources.keys() if context and context.resources else []),
        }

    return cast(OperationFunction, test_operation)


@pytest.fixture
def questionary_mock(mocker):
    """
    Provides a mock for the questionary module used in CLI operations.
    """
    return mocker.patch.object(operation, "questionary")


@pytest.fixture
def mock_context_selection(questionary_mock):
    """
    Factory fixture to set up mock context selection with specified context name.
    """

    def _mock_selection(context_name: str):
        questionary_mock.select.return_value.ask.return_value = context_name

    return _mock_selection


@pytest.fixture
def mock_resource_selection(questionary_mock):
    """
    Factory fixture to set up mock resource selection with specified resource names.
    """

    def _mock_selection(resource_names: list[str]):
        questionary_mock.checkbox.return_value.ask.return_value = resource_names
        return questionary_mock

    return _mock_selection


def assert_context_selection_calls(questionary_mock, expected_calls: int):
    """
    Helper function to assert the number of times context selection was called.
    """
    if expected_calls == 1:
        questionary_mock.select.assert_called_once()
    elif expected_calls == 0:
        questionary_mock.select.assert_not_called()
    else:
        assert questionary_mock.select.call_count == expected_calls


def assert_resource_selection_calls(questionary_mock, expected_calls: int):
    """
    Helper function to assert the number of times resource selection was called.
    """
    if expected_calls == 1:
        questionary_mock.checkbox.assert_called_once()
    elif expected_calls == 0:
        questionary_mock.checkbox.assert_not_called()
    else:
        assert questionary_mock.checkbox.call_count == expected_calls


def test_cli_operation_decorator(create_loaded_plugin, sample_context, empty_context, sample_operation):
    """
    Tests that the decorator preserves the original function's metadata and returns a callable function.
    Expects the wrapped function to have the same __name__, __doc__, and other attributes as the original.
    """
    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    assert callable(wrapped_operation)
    assert wrapped_operation.__name__ == sample_operation.__name__
    assert wrapped_operation.__doc__ == sample_operation.__doc__
    assert hasattr(wrapped_operation, "__wrapped__")
    assert wrapped_operation.__wrapped__ is sample_operation


def test_cli_operation_executes_with_provided_context_and_resources(
    create_loaded_plugin, sample_context, empty_context, sample_operation
):
    """
    Tests successful execution when context_name and resource_names are provided as parameters.
    Expects the operation to execute with the specified context and resources without interactive prompts.
    """
    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    result = wrapped_operation(context_name="test_context", resource_names=["resource1", "resource2"])

    assert result["context_name"] == "test_context"
    assert result["resource_names"] == ["resource1", "resource2"]


def test_cli_operation_executes_with_interactive_context_selection(
    questionary_mock,
    mock_context_selection,
    mock_resource_selection,
    create_loaded_plugin,
    sample_context,
    empty_context,
    sample_operation,
):
    """
    Tests successful execution when context_name and resource_names are not provided, triggering interactive selection.
    Expects the original function to be executed with filtered context after prompting user for context and resource
    selection and the wrapper to return the original function's result.
    """
    mock_context_selection("test_context")
    mock_resource_selection(["resource1"])

    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    result = wrapped_operation(context_name=None, resource_names=None)

    assert result["context_name"] == "test_context"
    assert_context_selection_calls(questionary_mock, 1)
    assert_resource_selection_calls(questionary_mock, 1)


def test_cli_operation_executes_with_additional_arguments(
    create_loaded_plugin, sample_context, empty_context, sample_operation
):
    """
    Tests decoration of functions that accept additional positional and keyword arguments beyond context.
    Expects all arguments to be properly passed through to the original function.
    """
    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    result = wrapped_operation(
        "positional_arg",
        context_name="test_context",
        resource_names=["resource1"],
        additional_arg="modified",
        extra_kwarg="extra_value",
    )

    assert result["args"] == ("positional_arg",)
    assert result["context_name"] == "test_context"
    assert result["resource_names"] == ["resource1"]
    assert result["kwargs"] == {"additional_arg": "modified", "extra_kwarg": "extra_value"}


def test_cli_operation_raises_error_when_no_contexts_available(create_loaded_plugin, sample_operation):
    """
    Tests that an exception is raised when the plugin has no available contexts.
    Expects the decorator to raise an exception with message indicating that the plugin has no contexts.
    """
    empty_plugin = create_loaded_plugin("empty_plugin", contexts={})
    wrapped_operation = cli_operation(empty_plugin, sample_operation)

    with pytest.raises(click.ClickException, match="No contexts available in plugin"):
        wrapped_operation(context_name=None, resource_names=None)


def test_cli_operation_raises_error_when_context_not_found(
    create_loaded_plugin, sample_context, empty_context, sample_operation
):
    """
    Tests that an exception is raised when the specified context_name does not exist in the plugin.
    Expects the decorator to raise an exception with message indicating that the context was not found.
    """
    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    with pytest.raises(click.ClickException, match="Context 'nonexistent_context' not found in plugin 'test_plugin'"):
        wrapped_operation(context_name="nonexistent_context", resource_names=["resource1"])


def test_cli_operation_raises_error_when_no_resources_available(
    create_loaded_plugin, sample_context, empty_context, sample_operation
):
    """
    Tests that an exception is raised when the selected context has no available resources.
    Expects the decorator to raise an exception with message indicating that the context has no resources.
    """
    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    with pytest.raises(click.ClickException, match="No resources available in context 'empty_context'"):
        wrapped_operation(context_name="empty_context", resource_names=[])


def test_cli_operation_raises_error_when_resource_not_found(
    create_loaded_plugin, sample_context, empty_context, sample_operation
):
    """
    Tests that an exception is raised when a specified resource_name does not exist in the context.
    Expects the decorator to raise an exception with message indicating that the resource was not found.
    """
    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    with pytest.raises(
        click.ClickException, match="Resource 'nonexistent_resource' not found in context 'test_context'"
    ):
        wrapped_operation(context_name="test_context", resource_names=["nonexistent_resource"])


def test_cli_operation_raises_error_when_multiple_invalid_resources(
    create_loaded_plugin, sample_context, empty_context, sample_operation
):
    """
    Tests that an exception is raised when multiple specified resource names do not exist in the context.
    Expects the decorator to raise an exception for the first invalid resource encountered.
    """
    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    with pytest.raises(click.ClickException, match="Resource 'invalid1' not found in context 'test_context'"):
        wrapped_operation(context_name="test_context", resource_names=["invalid1", "invalid2"])


def test_cli_operation_wraps_operation_exceptions(create_loaded_plugin, sample_context, empty_context):
    """
    Tests that exceptions raised by the original operation function are wrapped in OperationExecutionError.
    Expects any exception from the wrapped function to be caught and re-raised as OperationExecutionError with
    the original exception as the cause.
    """

    def failing_operation(context: Context):
        raise ValueError("Original operation error")

    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, failing_operation)

    with pytest.raises(OperationExecutionError, match="Could not execute operation: Original operation error"):
        wrapped_operation(context_name="test_context", resource_names=["resource1"])


def test_cli_operation_uses_single_context_automatically(create_loaded_plugin, sample_context, sample_operation):
    """
    Tests that when only one context is available, it is selected automatically without prompting.
    Expects the decorator to use the single available context without interactive selection.
    """
    single_context_plugin = create_loaded_plugin("single_plugin", contexts={"test_context": sample_context})
    wrapped_operation = cli_operation(single_context_plugin, sample_operation)

    result = wrapped_operation(context_name=None, resource_names=["resource1"])

    assert result["context_name"] == "test_context"


@pytest.mark.parametrize("resource_names", [None, []])
def test_cli_operation_executes_with_interactive_resource_selection(
    mock_resource_selection, create_loaded_plugin, sample_context, empty_context, sample_operation, resource_names
):
    """
    Tests that when resource_names is None or an empty list, interactive selection is triggered.
    Expects the decorator to prompt for resource selection when no resources are specified.
    """
    questionary_mock = mock_resource_selection(["resource1"])

    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    result = wrapped_operation(context_name="test_context", resource_names=resource_names)

    assert result["context_name"] == "test_context"
    assert_resource_selection_calls(questionary_mock, 1)
    assert_context_selection_calls(questionary_mock, 0)


def test_cli_operation_raises_error_when_no_resources_selected_interactively(
    mock_resource_selection, create_loaded_plugin, sample_context, empty_context, sample_operation
):
    """
    Tests that an exception is raised when the user selects no resources during interactive selection.
    Expects the decorator to raise an exception with message indicating that no resources were selected.
    """
    questionary_mock = mock_resource_selection([])

    contexts = {"test_context": sample_context, "empty_context": empty_context}
    loaded_plugin_with_contexts = create_loaded_plugin("test_plugin", contexts=contexts)
    wrapped_operation = cli_operation(loaded_plugin_with_contexts, sample_operation)

    with pytest.raises(click.ClickException, match="No resources selected"):
        wrapped_operation(context_name="test_context", resource_names=None)

    assert_resource_selection_calls(questionary_mock, 1)
    assert_context_selection_calls(questionary_mock, 0)
