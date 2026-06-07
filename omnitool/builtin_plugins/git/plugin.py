import logging

from omnitool.plugin.api.context import Context
from omnitool.plugin.api.definition import PluginDefinition

logger = logging.getLogger(__name__)

class GitRepository:
    pass


definition = PluginDefinition(root_operation_name="git", resource_data_type=GitRepository)


@definition.operation
def checkout(branch: str, context: Context) -> None:
    """
    Checks out a branch in the git repository.
    """
    logger.info(f"Checking out branch: {branch}")


@definition.context_loader
def load_context(context: Context) -> None:
    """
    Loads the context for the git plugin.
    """
    logger.info("Loading context for git plugin")
