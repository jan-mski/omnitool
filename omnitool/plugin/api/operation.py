from dataclasses import dataclass
from typing import Protocol, Any, Callable

from omnitool.plugin.api.context import Context


class OperationProtocol(Protocol):
    def __call__(self, *args: Any, context: Context, **kwargs: Any) -> Any:
        """
        Protocol for plugin operation functions that can be registered in operation groups.

        Operation functions must accept a context as keyword-only argument, along with any other positional
        and keyword arguments.
        The context will contain only the resources that are selected for the operation.

        Args:
            *args: Variable positional arguments passed to the operation
            context: Context on which the operation is being performed, with the selected resources
            **kwargs: Additional keyword arguments passed to the operation

        Returns:
            Result of the operation call
        """
        ...


@dataclass
class PluginOperationGroup:
    """
    Registry for plugin operations.
    """
    root_operation_name: str
    subgroups: list["PluginOperationGroup"]
    operations: list[OperationProtocol]

    def __init__(self, name: str = None) -> None:
        self.root_operation_name = name
        self.subgroups = []
        self.operations = []

    def add_subgroup(self, subgroup: "PluginOperationGroup") -> None:
        """
        Adds a subgroup to the plugin operation group.

        Args:
            subgroup: The subgroup to add
        """
        if not isinstance(subgroup, PluginOperationGroup):
            raise TypeError("Subgroup must be of type PluginOperationGroup")

        self.subgroups.append(subgroup)

    def operation(self, func: OperationProtocol = None) -> (
            OperationProtocol | Callable[[OperationProtocol], OperationProtocol]):
        """
        Decorator to register a method as a resource operation.

        Can be used in two ways:
            - @definition.operation
            - @definition.operation()

        Args:
            func: The function to register, or None if called with parentheses

        Returns:
            The registered function, unchanged, or a decorator function if called with parentheses
        """

        def decorator(f: OperationProtocol) -> OperationProtocol:
            if f is None:
                raise ValueError("Function cannot be None")

            self.operations.append(f)

            return f

        if func is not None:
            return decorator(func)

        return decorator
