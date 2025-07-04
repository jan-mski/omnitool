from dataclasses import dataclass
from typing import Optional, Any, Callable

OperationFunction = Callable[..., Any]


@dataclass
class PluginOperationGroup:
    """
    Registry for plugin operations.
    """

    root_operation_name: Optional[str]
    subgroups: list["PluginOperationGroup"]
    operations: list[OperationFunction]

    def __init__(self, name: Optional[str] = None) -> None:
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

    def operation(
        self, operation: Optional[OperationFunction] = None
    ) -> OperationFunction | Callable[[OperationFunction], OperationFunction]:
        """
        Decorator to register a method as a resource operation.

        Operation functions should accept a context as keyword argument named 'context', along with any other positional
        and keyword arguments. The context will contain only the resources that are selected for the operation.

        Can be used in two ways:
            - @definition.operation
            - @definition.operation()

        Args:
            operation: The function to register, or None if called with parentheses

        Returns:
            The registered function, unchanged, or a decorator function if called with parentheses
        """

        def wrapper(op: Optional[OperationFunction] = None):
            if op is None:
                raise ValueError("Function cannot be None")

            self.operations.append(op)

            return op

        if operation is not None:
            return wrapper(operation)

        return wrapper
