import functools
import logging
from typing import List, Optional

import click
import questionary
from typer import Option

from omnitool.plugin.api.context import Context, Resource
from omnitool.plugin.api.operation import OperationProtocol
from omnitool.plugin.loading.loader import LoadedPlugin


logger = logging.getLogger(__name__)


class OperationExecutionError(Exception):
    def __init__(self, additional_info: str):
        super().__init__(f"Could not execute operation: {additional_info}")


def cli_operation(plugin: LoadedPlugin, operation: OperationProtocol) -> OperationProtocol:
    """
    Decorator that wraps plugin operations for CLI execution.

    This decorator transforms plugin operations into CLI commands by:
    1. Adding CLI argument parsing for context and resource selection
    2. Handling interactive prompts when arguments are not provided
    3. Creating a filtered context with only selected resources
    4. Passing the context to the operation function

    The decorator adds two CLI options to the wrapped function:
    - --context: Specify context name (optional, will prompt if not provided)
    - --resource: Specify resource names (optional, will prompt if not provided)

    Args:
        plugin: The loaded plugin containing contexts and operations
        operation: The operation function to wrap (must accept a 'context' keyword argument)

    Returns:
        A wrapped operation function that can be used as a CLI command
    """

    @functools.wraps(operation)
    def wrapper(
        *args,
        context_name: str = Option(None, "--context", help="Context name to use for resolving resources"),
        resource_names: List[str] = Option(None, "--resource", help="Resource names to operate on"),
        **kwargs,
    ):
        operation_name = operation.__name__
        logger.info(f"Executing operation '{operation_name}'")

        selected_context = _select_context(plugin, context_name)
        selected_resources = _select_resources(selected_context, resource_names)
        operation_context = Context(name=selected_context.name, resources=selected_resources)

        try:
            result = operation(*args, context=operation_context, **kwargs)
        except Exception as e:
            raise OperationExecutionError(str(e)) from e

        logger.info(f"Completed operation '{operation_name}'")
        return result

    return wrapper


def _select_context(plugin: LoadedPlugin, context_name: Optional[str] = None) -> Context:
    available_contexts = list(plugin.data.contexts.keys())
    if not available_contexts:
        raise click.ClickException("No contexts available in plugin")

    if context_name:
        if context_name not in plugin.data.contexts:
            raise click.ClickException(f"Context '{context_name}' not found in plugin '{plugin.name}'")
        logger.info(f"Using specified context: {context_name}")
    elif len(available_contexts) == 1:
        context_name = available_contexts[0]
        logger.info(f"Using default context: {context_name}")
    else:
        context_name = questionary.select("Select a context:", choices=available_contexts).ask()

    return plugin.data.contexts[context_name]


def _select_resources(selected_context: Context, resource_names: Optional[List[str]] = None) -> dict[str, Resource]:
    available_resources = list(selected_context.resources.keys())
    if not available_resources:
        raise click.ClickException(f"No resources available in context '{selected_context.name}'")

    if resource_names:
        _validate_resource_names(selected_context, resource_names)
    else:
        resource_names = questionary.checkbox("Select resources:", choices=available_resources).ask()

    return {name: selected_context.resources[name] for name in resource_names}


def _validate_resource_names(context: Context, resource_names: List[str]) -> None:
    for resource_name in resource_names:
        if resource_name not in context.resources:
            raise click.ClickException(f"Resource '{resource_name}' not found in context '{context.name}'")
