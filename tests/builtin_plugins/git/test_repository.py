
from __future__ import annotations

import pytest

from omnitool.builtin_plugins.git.exceptions import RepositoryAccessException
from omnitool.builtin_plugins.git.repository import GitRepository
from dulwich.porcelain import add


def test_gitrepository_init(git_repo):
    repo = GitRepository(name="test_repo", path=git_repo.path)
    assert repo.name == "test_repo"
    assert repo.path == git_repo.path


def test_gitrepository_init_invalid_path():
    with pytest.raises(RepositoryAccessException):
        GitRepository(name="test_repo", path="/invalid/path")


def test_get_current_branch(git_repo):
    repo = GitRepository(name="test_repo", path=git_repo.path)
    assert repo.get_current_branch() == "master"


def test_get_branches(git_repo):
    repo = GitRepository(name="test_repo", path=git_repo.path)
    assert repo.get_branches() == ["master"]

    # Create a new branch
    git_repo.refs[b'refs/heads/develop'] = git_repo.head()
    assert sorted(repo.get_branches()) == ["develop", "master"]


def test_get_remote_branches(git_repo):
    repo = GitRepository(name="test_repo", path=git_repo.path)
    assert repo.get_remote_branches() == []

    # Create a remote branch
    git_repo.refs[b'refs/remotes/origin/master'] = git_repo.head()
    assert repo.get_remote_branches() == ["origin/master"]


def test_is_dirty(git_repo):
    repo = GitRepository(name="test_repo", path=git_repo.path)
    assert not repo.is_dirty()

    # Modify a file
    file_path = f"{git_repo.path}/test.txt"
    with open(file_path, "w") as f:
        f.write("hello")
    
    add(git_repo, [file_path])
    assert repo.is_dirty()
