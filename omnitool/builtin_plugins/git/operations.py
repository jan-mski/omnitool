import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from dulwich import porcelain
from dulwich.errors import NotGitRepository

from omnitool.plugin.api.context import Context

from .repository import GitRepository, RepositoryAccessException

logger = logging.getLogger(__name__)


async def checkout(branch: str, create: bool = False, context: Context = None) -> None:
    """
    Checks out a branch in git repositories.

    Single operation that handles both branch switching and creation, mirroring git's interface.

    Args:
        branch: Name of the branch to checkout
        create: If True, create the branch (equivalent to `git checkout -b`)
        context: Omnitool context containing GitRepository resources

    Raises:
        RepositoryAccessException: For various git operation errors
    """
    if context is None or not context.resources:
        logger.warning("No repositories found in context")
        return

    repositories = [
        resource.data for resource in context.resources.values() if isinstance(resource.data, GitRepository)
    ]

    if not repositories:
        logger.warning("No GitRepository resources found in context")
        return

    logger.info(f"Starting checkout operation on {len(repositories)} repositories")

    # Execute checkout operations asynchronously
    results = await _execute_checkout_async(repositories, branch, create)

    # Log results
    succeeded = sum(1 for success, _ in results if success)
    failed = len(results) - succeeded

    logger.info(f"Checkout completed: {succeeded} succeeded, {failed} failed")

    # Log individual results
    for i, (success, message) in enumerate(results):
        repo = repositories[i]
        if success:
            if create:
                logger.info(f"Repository {repo.path}: Created and checked out branch '{branch}'")
            else:
                logger.info(f"Repository {repo.path}: Checked out branch '{branch}'")
        else:
            logger.error(f"Repository {repo.path}: {message}")


async def _execute_checkout_async(
    repositories: List[GitRepository], branch: str, create: bool
) -> List[Tuple[bool, str]]:
    """
    Execute checkout operations on multiple repositories asynchronously.

    Args:
        repositories: List of GitRepository objects
        branch: Branch name to checkout
        create: Whether to create the branch

    Returns:
        List of (success, message) tuples for each repository
    """
    loop = asyncio.get_event_loop()

    # Use ThreadPoolExecutor to run git operations in parallel
    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, _checkout_single_repository, repo, branch, create) for repo in repositories
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failure results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append((False, str(result)))
            else:
                processed_results.append(result)

        return processed_results


def _checkout_single_repository(repo: GitRepository, branch: str, create: bool) -> Tuple[bool, str]:
    """
    Perform checkout operation on a single repository.

    Args:
        repo: GitRepository object
        branch: Branch name to checkout
        create: Whether to create the branch

    Returns:
        Tuple of (success, message)
    """
    try:
        logger.debug(f"Processing checkout for repository: {repo.path}")

        dulwich_repo = repo.repo

        if create:
            # Check if branch already exists
            branch_ref = f"refs/heads/{branch}".encode("utf-8")
            if branch_ref in dulwich_repo.refs:
                raise RepositoryAccessException(f"A branch named '{branch}' already exists")

            # Create and checkout new branch
            logger.debug(f"Creating new branch '{branch}' in {repo.path}")

            # Get current HEAD commit
            current_head = dulwich_repo.refs[b"HEAD"]

            # Create new branch reference pointing to current HEAD
            dulwich_repo.refs[branch_ref] = current_head

            # Update HEAD to point to new branch
            dulwich_repo.refs[b"HEAD"] = branch_ref

            # Update working tree
            porcelain.reset(dulwich_repo, "hard")

        else:
            # Check if branch exists
            branch_ref = f"refs/heads/{branch}".encode("utf-8")
            if branch_ref not in dulwich_repo.refs:
                raise RepositoryAccessException(f"Branch '{branch}' does not exist")

            # Checkout existing branch
            logger.debug(f"Checking out existing branch '{branch}' in {repo.path}")

            # Update HEAD to point to the branch
            dulwich_repo.refs[b"HEAD"] = branch_ref

            # Update working tree
            porcelain.reset(dulwich_repo, "hard")

        return (True, f"Successfully checked out branch '{branch}'")

    except NotGitRepository:
        error_msg = f"Not a git repository: {repo.path}"
        logger.debug(error_msg)
        return (False, error_msg)
    except PermissionError:
        error_msg = f"Permission denied: {repo.path}"
        logger.debug(error_msg)
        return (False, error_msg)
    except RepositoryAccessException as e:
        logger.debug(f"Repository access error in {repo.path}: {str(e)}")
        return (False, str(e))
    except Exception as e:
        error_msg = f"Unexpected error in {repo.path}: {str(e)}"
        logger.debug(error_msg, exc_info=True)
        return (False, error_msg)
