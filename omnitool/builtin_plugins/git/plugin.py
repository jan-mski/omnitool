import logging

from dulwich.errors import NotGitRepository

from omnitool.plugin.api.context import Context
from omnitool.plugin.api.definition import PluginDefinition

from .operations import checkout
from .repository import GitRepository, RepositoryAccessException

logger = logging.getLogger(__name__)

definition = PluginDefinition(root_operation_name="git", resource_data_type=GitRepository)


@definition.operation
async def checkout_operation(branch: str, context: Context, create: bool = False) -> None:
    """
    Checks out a branch in the git repository.

    Args:
        branch: Name of the branch to checkout
        context: Omnitool context containing GitRepository resources
        create: If True, create the branch (equivalent to `git checkout -b`)
    """
    await checkout(branch, create, context)


@definition.context_loader
def load_context(context: Context) -> None:
    """
    Loads the context for the git plugin.

    Initializes GitRepository objects from the context and validates
    that paths point to valid git repositories.

    Args:
        context: The context containing resources to initialize

    Raises:
        RepositoryAccessException: If a path is not a valid git repository
    """
    logger.debug(f"Loading git context with {len(context.resources)} resources")

    for resource_name, resource in context.resources.items():
        try:
            # Validate that the path points to a valid git repository
            repo_path = resource.location.path

            # Check if path exists and is a directory
            if not repo_path.exists():
                raise RepositoryAccessException(f"Path does not exist: {repo_path}")

            if not repo_path.is_dir():
                raise RepositoryAccessException(f"Path is not a directory: {repo_path}")

            # Try to open as git repository to validate and create Repo instance
            try:
                from dulwich.repo import Repo

                repo_instance = Repo(str(repo_path))
            except NotGitRepository:
                raise RepositoryAccessException(f"Not a git repository: {repo_path}")

            # Create GitRepository instance with Repo instance
            git_repo = GitRepository(repo_instance)
            resource.data = git_repo

            logger.debug(f"Initialized GitRepository for {resource_name} at {repo_path}")

        except Exception as e:
            logger.error(f"Failed to initialize git repository for {resource_name}: {str(e)}")
            raise RepositoryAccessException(f"Failed to initialize {resource_name}: {str(e)}")

    logger.debug("Git context loading completed successfully")
