import logging
from pathlib import Path

import pygit2
from omnitool.plugin.api.context import Context
from omnitool.plugin.api.definition import PluginDefinition


logger = logging.getLogger(__name__)


class GitRepository:
    def __init__(self, path: Path) -> None:
        self._repo = pygit2.Repository(path)

    def checkout(self, branch: str) -> None:
        self._repo.checkout(self._repo.branches[branch])


definition = PluginDefinition(root_operation_name="git", resource_data_type=GitRepository)


@definition.operation
def checkout(branch: str, context: Context) -> None:
    for resource in context.resources.values():
        repo: GitRepository = resource.data
        repo.checkout(branch)


@definition.context_loader
def load_context(context: Context) -> None:
    for resource in context.resources.values():
        resource.data = GitRepository(resource.location.path)
