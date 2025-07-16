from pathlib import Path

import pytest


@pytest.fixture
def mock_dulwich(mocker):
    """Mock dulwich library components for testing."""
    mock_repo = mocker.patch("omnitool.builtin_plugins.git.repository.Repo")
    mock_porcelain = mocker.patch("omnitool.builtin_plugins.git.repository.porcelain")
    mock_not_git_repo = mocker.patch("omnitool.builtin_plugins.git.repository.NotGitRepository")

    # Also mock in operations module
    mocker.patch("omnitool.builtin_plugins.git.operations.porcelain", mock_porcelain)
    mocker.patch("omnitool.builtin_plugins.git.operations.NotGitRepository", mock_not_git_repo)

    # Also mock in plugin module
    mocker.patch("omnitool.builtin_plugins.git.plugin.Repo", mock_repo)
    mocker.patch("omnitool.builtin_plugins.git.plugin.NotGitRepository", mock_not_git_repo)

    return {"repo": mock_repo, "porcelain": mock_porcelain, "not_git_repo": mock_not_git_repo}


@pytest.fixture
def sample_repo_path(tmp_path) -> Path:
    """Create a temporary directory path for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    return repo_path
