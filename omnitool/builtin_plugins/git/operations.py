
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dulwich.porcelain import checkout as dulwich_checkout

from omnitool.builtin_plugins.git.exceptions import RepositoryAccessException

if TYPE_CHECKING:
    from omnitool.builtin_plugins.git.repository import GitRepository

logger = logging.getLogger(__name__)


def checkout(
    repo: GitRepository,
    branch: str,
    create: bool = False,
) -> None:
    branch_b = branch.encode('utf-8')
    branches = repo.get_branches()

    if create:
        if branch in branches:
            raise RepositoryAccessException(
                f"A branch named '{branch}' already exists"
            )
        logger.debug(f"Creating and checking out branch '{branch}'")
        head_sha = repo._repo.head()
        branch_ref = f"refs/heads/{branch}".encode('utf-8')
        repo._repo.refs[branch_ref] = head_sha
        repo._repo.refs.set_symbolic_ref(b'HEAD', branch_ref)

    else:
        if branch not in branches:
            raise RepositoryAccessException(f"Branch '{branch}' does not exist")
        logger.debug(f"Checking out branch '{branch}'")
        dulwich_checkout(repo._repo, branch.encode('utf-8'))
        repo._repo.refs.set_symbolic_ref(b'HEAD', f'refs/heads/{branch}'.encode('utf-8'))
