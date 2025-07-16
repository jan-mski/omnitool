
from __future__ import annotations

import pytest

from omnitool.builtin_plugins.git.operations import checkout
from omnitool.builtin_plugins.git.exceptions import RepositoryAccessException
from omnitool.builtin_plugins.git.repository import (
    GitRepository,
)


@pytest.fixture
def git_repository(git_repo) -> GitRepository:
    return GitRepository(name="test_repo", path=git_repo.path)


def test_checkout_existing_branch(git_repository: GitRepository):
    # Create a new branch
    git_repository._repo.refs[b'refs/heads/develop'] = git_repository._repo.head()
    
    checkout(git_repository, "develop")
    assert git_repository.get_current_branch() == "develop"


def test_checkout_nonexistent_branch_fails(git_repository: GitRepository):
    with pytest.raises(RepositoryAccessException, match="Branch 'develop' does not exist"):
        checkout(git_repository, "develop")


def test_checkout_create_branch(git_repository: GitRepository):
    checkout(git_repository, "feature/new-feature", create=True)
    assert git_repository.get_current_branch() == "feature/new-feature"
    assert "feature/new-feature" in git_repository.get_branches()


def test_checkout_create_existing_branch_fails(git_repository: GitRepository):
    with pytest.raises(RepositoryAccessException, match="A branch named 'master' already exists"):
        checkout(git_repository, "master", create=True)
