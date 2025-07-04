from omnitool.plugin.api.context import Context, ResourceData
from omnitool.plugin.api.definition import PluginDefinition


class GitRepository(ResourceData):
    pass


definition = PluginDefinition(root_operation_name="git", resource_data_type=GitRepository)


@definition.operation
def checkout(branch: str, context: Context) -> None:
    """
    Checks out a branch in the git repository.
    """
    print("Checking out branch:", branch)


@definition.context_loader
def load_context(context: Context) -> None:
    """
    Loads the context for the git plugin.
    """
    print("Loading context for git plugin")
