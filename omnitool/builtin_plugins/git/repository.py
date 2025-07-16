from __future__ import annotations

from dataclasses import dataclass
from typing import List

from dulwich.porcelain import status
from dulwich.refs import parse_symref_value
from dulwich.repo import Repo

from omnitool.builtin_plugins.git.exceptions import RepositoryAccessException
from omnitool.plugin.api.context import ResourceData

@dataclass
class GitRepository(ResourceData):
    name: str
    path: str
    _repo: Repo | None = None

    def __post_init__(self):
        try:
            self._repo = Repo(self.path)
        except Exception as e:
            raise RepositoryAccessException(f"Not a git repository: {self.path}") from e

    def get_current_branch(self) -> str:
        try:
            symref = self._repo.refs.read_ref(b'HEAD')
            ref = parse_symref_value(symref)
            if ref is None:
                raise RepositoryAccessException("Detached HEAD")
            return ref.decode('utf-8').replace('refs/heads/', '')
        except Exception as e:
            raise RepositoryAccessException(f"Failed to get current branch: {e}") from e

    def get_branches(self) -> List[str]:
        try:
            refs = self._repo.get_refs()
            return [
                ref.decode('utf-8').replace('refs/heads/', '')
                for ref in refs
                if ref.startswith(b'refs/heads/')
            ]
        except Exception as e:
            raise RepositoryAccessException(f"Failed to get branches: {e}") from e

    def get_remote_branches(self) -> List[str]:
        try:
            refs = self._repo.get_refs()
            return [
                ref.decode('utf-8').replace('refs/remotes/', '')
                for ref in refs
                if ref.startswith(b'refs/remotes/')
            ]
        except Exception as e:
            raise RepositoryAccessException(f"Failed to get remote branches: {e}") from e

    def is_dirty(self) -> bool:
        try:
            # Dulwich status returns a tuple of (staged, unstaged, untracked)
            # We consider the repo dirty if there are any staged or unstaged changes.
            staged, unstaged, _ = status(self._repo)
            return bool(staged['add']) or bool(staged['delete']) or bool(staged['modify']) or bool(unstaged)
        except Exception as e:
            raise RepositoryAccessException(f"Failed to get repository status: {e}") from e