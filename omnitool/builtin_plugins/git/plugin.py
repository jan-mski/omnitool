
from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, cast

import typer

from omnitool.builtin_plugins.git.operations import checkout as checkout_branch
from omnitool.builtin_plugins.git.exceptions import RepositoryAccessException
from omnitool.builtin_plugins.git.repository import (
    GitRepository,
)
from omnitool.plugin.api.context import Context, ContextLoader, Resource
from omnitool.plugin.api.definition import Operation, PluginDefinition

logger = logging.getLogger(__name__)


async def checkout_operation(
    context: Context,
    branch: str = typer.Argument(..., help="Name of the branch to checkout"),
    create: bool = typer.Option(
        False, "--create", "-b",
        help="Create a new branch and switch to it",
    ),
) -> None:
    repos = cast(List[GitRepository], context.get_resources(GitRepository))
    logger.info(f"Starting checkout operation on {len(repos)} repositories")

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(
                executor, checkout_branch, repo, branch, create,
            )
            for repo in repos
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    succeeded = 0
    failed = 0
    for repo, result in zip(repos, results):
        if isinstance(result, Exception):
            failed += 1
            logger.error(
                f"Repository {repo.path}: Failed to checkout branch '{branch}': "
                f"{result}"
            )
        else:
            succeeded += 1
            if create:
                logger.info(
                    f"Repository {repo.path}: "
                    f"Created and checked out branch '{branch}'"
                )
            else:
                logger.info(
                    f"Repository {repo.path}: Checked out branch '{branch}'"
                )

    logger.info(f"Checkout completed: {succeeded} succeeded, {failed} failed")


def git_context_loader(resource: Resource) -> ContextLoader:
    def loader() -> GitRepository:
        try:
            return GitRepository(name=resource.name, path=str(resource.location.path))
        except RepositoryAccessException as e:
            logger.error(f"Failed to load repository {resource.location.path}: {e}")
            raise
    return loader


definition = PluginDefinition(
    name="git",
    description="Git repository management",
    operations={
        "checkout": Operation(
            help="Checkout a branch",
            function=checkout_operation,
        ),
    },
    context_loader=git_context_loader,
)
