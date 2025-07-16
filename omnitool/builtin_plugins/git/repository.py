import logging
from pathlib import Path
from typing import List

from dulwich import porcelain
from dulwich.errors import NotGitRepository
from dulwich.repo import Repo

from omnitool.plugin.api.context import ResourceData

logger = logging.getLogger(__name__)


class RepositoryAccessException(Exception):
    """
    Exception raised when there's an error accessing a git repository.
    """

    pass


class GitRepository(ResourceData):
    """
    Represents a git repository with operations for branch management.
    """

    def __init__(self, repo: Repo):
        """
        Initialize GitRepository with a Repo instance.

        Args:
            repo: The dulwich Repo instance
        """
        self.repo = repo

    @property
    def path(self) -> Path:
        """
        Get the path to the repository.

        Returns:
            Path: The absolute path to the git repository
        """
        return Path(self.repo.path)

    def get_current_branch(self) -> str:
        """
        Returns the currently checked out branch name.

        Returns:
            str: The name of the current branch

        Raises:
            RepositoryAccessException: If there's an error accessing the repository
        """
        try:
            head = self.repo.refs[b"HEAD"]

            # Find which branch HEAD points to
            for ref_name in self.repo.refs.keys():
                if ref_name.startswith(b"refs/heads/") and self.repo.refs[ref_name] == head:
                    return ref_name.decode("utf-8").replace("refs/heads/", "")

            # If no branch found, check if we're in detached HEAD
            if head:
                return head.decode("utf-8")[:8]  # Short hash for detached HEAD

            raise RepositoryAccessException("Could not determine current branch")

        except NotGitRepository:
            raise RepositoryAccessException(f"Not a git repository: {self.path}")
        except Exception as e:
            raise RepositoryAccessException(f"Error getting current branch: {str(e)}")

    def get_branches(self) -> List[str]:
        """
        Returns a list of all local branches.

        Returns:
            List[str]: List of local branch names

        Raises:
            RepositoryAccessException: If there's an error accessing the repository
        """
        try:
            branches = []

            for ref_name in self.repo.refs.keys():
                if ref_name.startswith(b"refs/heads/"):
                    branch_name = ref_name.decode("utf-8").replace("refs/heads/", "")
                    branches.append(branch_name)

            return sorted(branches)

        except NotGitRepository:
            raise RepositoryAccessException(f"Not a git repository: {self.path}")
        except Exception as e:
            raise RepositoryAccessException(f"Error getting branches: {str(e)}")

    def get_remote_branches(self) -> List[str]:
        """
        Returns a list of all remote branches.

        Returns:
            List[str]: List of remote branch names

        Raises:
            RepositoryAccessException: If there's an error accessing the repository
        """
        try:
            remote_branches = []

            for ref_name in self.repo.refs.keys():
                if ref_name.startswith(b"refs/remotes/"):
                    branch_name = ref_name.decode("utf-8").replace("refs/remotes/", "")
                    remote_branches.append(branch_name)

            return sorted(remote_branches)

        except NotGitRepository:
            raise RepositoryAccessException(f"Not a git repository: {self.path}")
        except Exception as e:
            raise RepositoryAccessException(f"Error getting remote branches: {str(e)}")

    def is_dirty(self) -> bool:
        """
        Returns whether the repository has uncommitted changes.

        Returns:
            bool: True if there are uncommitted changes, False otherwise

        Raises:
            RepositoryAccessException: If there's an error accessing the repository
        """
        try:
            # Check for uncommitted changes in the index and working tree
            # Using porcelain.status to get a comprehensive status
            status = porcelain.status(str(self.path))

            # If any of the status dictionaries have entries, the repo is dirty
            return bool(status.staged or status.unstaged or status.untracked)

        except NotGitRepository:
            raise RepositoryAccessException(f"Not a git repository: {self.path}")
        except Exception as e:
            raise RepositoryAccessException(f"Error checking repository status: {str(e)}")
