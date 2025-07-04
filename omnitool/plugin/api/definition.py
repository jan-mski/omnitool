from typing import Optional, Type, Protocol, Callable

from omnitool.plugin.api.context import ResourceData, Context
from omnitool.plugin.api.operation import PluginOperationGroup


class ContextLoaderProtocol(Protocol):
    def __call__(self, context: Context) -> None:
        """
        Protocol for context loader functions that can be registered with the context_loader decorator.

        Context loader functions must accept a context as keyword-only arguments.
        They should load the resources and update the resource objects with the loaded data.

        Args:
            context: The context to load resources for.
        """
        ...


class PluginDefinition(PluginOperationGroup):
    """
    Base class for all plugin definitions.
    """

    resource_data_type: Optional[Type[ResourceData]] = None
    context_loader_function: Optional[ContextLoaderProtocol] = None

    def __init__(self, *, root_operation_name: str, resource_data_type: Optional[Type[ResourceData]] = None) -> None:
        super().__init__(root_operation_name)

        if resource_data_type and (
                not issubclass(resource_data_type, ResourceData) or
                resource_data_type is ResourceData):
            raise ValueError("Resource type must be a subclass of ResourceData")

        self.resource_data_type = resource_data_type

    def context_loader(self, func: Optional[ContextLoaderProtocol] = None) -> (
            ContextLoaderProtocol | Callable[[ContextLoaderProtocol], ContextLoaderProtocol]):
        """
        Decorator to register a method as a context loader.

        Can be used in two ways:
            - @definition.context_loader
            - @definition.context_loader()

        Args:
            func: The function to register, or None if called with parentheses

        Returns:
            The registered function, unchanged, or a decorator function if called with parentheses
        """

        def decorator(f: ContextLoaderProtocol) -> ContextLoaderProtocol:
            if f is None:
                raise ValueError("Function cannot be None")

            self.context_loader_function = f

            return f

        if func is not None:
            return decorator(func)

        return decorator
