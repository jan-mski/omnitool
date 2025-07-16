from pathlib import Path
from unittest.mock import Mock

import pytest

from omnitool.builtin_plugins.git.repository import GitRepository, RepositoryAccessException


class TestGitRepository:
    """Test cases for GitRepository class."""

    def test_init(self):
        """Test GitRepository initialization."""
        mock_repo_instance = Mock()
        mock_repo_instance.path = "/test/repo/path"

        repo = GitRepository(mock_repo_instance)
        assert repo.repo == mock_repo_instance
        assert str(repo.path) == "/test/repo/path"
        assert isinstance(repo.path, Path)

    def test_get_current_branch_success(self):
        """Test getting current branch successfully."""
        mock_repo = Mock()
        mock_repo.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/feature/test": b"commit_hash_feature",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo.path = "/test/repo"

        git_repository = GitRepository(mock_repo)
        current_branch = git_repository.get_current_branch()

        assert current_branch == "main"

    def test_get_current_branch_detached_head(self):
        """Test getting current branch when in detached HEAD state."""
        mock_repo = Mock()
        mock_repo.refs = {
            b"HEAD": b"commit_hash_detached",
            b"refs/heads/main": b"different_commit_hash",
        }
        mock_repo.path = "/test/repo"

        git_repository = GitRepository(mock_repo)
        current_branch = git_repository.get_current_branch()

        # Should return first 8 characters of commit hash
        assert current_branch == "commit_h"

    def test_get_current_branch_not_git_repo(self, mock_dulwich):
        """Test error when path is not a git repository."""
        mock_repo = Mock()
        mock_repo.refs = {b"HEAD": b"commit_hash"}
        mock_repo.path = "/test/repo"

        # Mock the refs access to raise NotGitRepository
        def refs_access_side_effect(key):
            raise mock_dulwich["not_git_repo"]("Not a git repository")

        mock_repo.refs.__getitem__.side_effect = refs_access_side_effect

        git_repository = GitRepository(mock_repo)

        with pytest.raises(RepositoryAccessException) as exc_info:
            git_repository.get_current_branch()

        assert "Not a git repository" in str(exc_info.value)

    def test_get_current_branch_other_error(self):
        """Test error handling for other exceptions."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        # Mock refs access to raise a general exception
        mock_repo.refs.__getitem__.side_effect = Exception("Permission denied")

        git_repository = GitRepository(mock_repo)

        with pytest.raises(RepositoryAccessException) as exc_info:
            git_repository.get_current_branch()

        assert "Error getting current branch" in str(exc_info.value)

    def test_get_branches_success(self):
        """Test getting list of local branches."""
        mock_repo = Mock()
        mock_repo.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/feature/test": b"commit_hash_feature",
            b"refs/heads/develop": b"commit_hash_develop",
            b"refs/remotes/origin/main": b"commit_hash_main",
        }
        mock_repo.path = "/test/repo"

        git_repository = GitRepository(mock_repo)
        branches = git_repository.get_branches()

        expected_branches = ["develop", "feature/test", "main"]
        assert branches == expected_branches

    def test_get_branches_empty_repo(self):
        """Test getting branches from empty repository."""
        mock_repo = Mock()
        mock_repo.refs = {b"HEAD": b"commit_hash"}
        mock_repo.path = "/test/repo"

        git_repository = GitRepository(mock_repo)
        branches = git_repository.get_branches()

        assert branches == []

    def test_get_branches_not_git_repo(self, mock_dulwich):
        """Test error when getting branches from non-git directory."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        # Mock the refs.keys() to raise NotGitRepository
        mock_repo.refs.keys.side_effect = mock_dulwich["not_git_repo"]("Not a git repository")

        git_repository = GitRepository(mock_repo)

        with pytest.raises(RepositoryAccessException) as exc_info:
            git_repository.get_branches()

        assert "Not a git repository" in str(exc_info.value)

    def test_get_remote_branches_success(self):
        """Test getting list of remote branches."""
        mock_repo = Mock()
        mock_repo.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
            b"refs/remotes/origin/main": b"commit_hash_main",
            b"refs/remotes/origin/develop": b"commit_hash_develop",
        }
        mock_repo.path = "/test/repo"

        git_repository = GitRepository(mock_repo)
        remote_branches = git_repository.get_remote_branches()

        expected_remote_branches = ["origin/develop", "origin/main"]
        assert remote_branches == expected_remote_branches

    def test_get_remote_branches_no_remotes(self):
        """Test getting remote branches when no remotes exist."""
        mock_repo = Mock()
        mock_repo.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
        }
        mock_repo.path = "/test/repo"

        git_repository = GitRepository(mock_repo)
        remote_branches = git_repository.get_remote_branches()

        assert remote_branches == []

    def test_get_remote_branches_error(self):
        """Test error handling when getting remote branches."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        # Mock refs.keys() to raise an exception
        mock_repo.refs.keys.side_effect = Exception("Network error")

        git_repository = GitRepository(mock_repo)

        with pytest.raises(RepositoryAccessException) as exc_info:
            git_repository.get_remote_branches()

        assert "Error getting remote branches" in str(exc_info.value)

    def test_is_dirty_clean_repo(self, mock_dulwich):
        """Test is_dirty returns False for clean repository."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        mock_status = Mock()
        mock_status.staged = {}
        mock_status.unstaged = {}
        mock_status.untracked = []

        mock_dulwich["porcelain"].status.return_value = mock_status

        git_repository = GitRepository(mock_repo)
        result = git_repository.is_dirty()

        assert result is False
        mock_dulwich["porcelain"].status.assert_called_once_with("/test/repo")

    def test_is_dirty_staged_changes(self, mock_dulwich):
        """Test is_dirty returns True when there are staged changes."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        mock_status = Mock()
        mock_status.staged = {"file1.txt": "modified"}
        mock_status.unstaged = {}
        mock_status.untracked = []

        mock_dulwich["porcelain"].status.return_value = mock_status

        git_repository = GitRepository(mock_repo)
        result = git_repository.is_dirty()

        assert result is True

    def test_is_dirty_unstaged_changes(self, mock_dulwich):
        """Test is_dirty returns True when there are unstaged changes."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        mock_status = Mock()
        mock_status.staged = {}
        mock_status.unstaged = {"file2.txt": "modified"}
        mock_status.untracked = []

        mock_dulwich["porcelain"].status.return_value = mock_status

        git_repository = GitRepository(mock_repo)
        result = git_repository.is_dirty()

        assert result is True

    def test_is_dirty_untracked_files(self, mock_dulwich):
        """Test is_dirty returns True when there are untracked files."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        mock_status = Mock()
        mock_status.staged = {}
        mock_status.unstaged = {}
        mock_status.untracked = ["new_file.txt"]

        mock_dulwich["porcelain"].status.return_value = mock_status

        git_repository = GitRepository(mock_repo)
        result = git_repository.is_dirty()

        assert result is True

    def test_is_dirty_not_git_repo(self, mock_dulwich):
        """Test is_dirty error handling for non-git repository."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        mock_dulwich["porcelain"].status.side_effect = mock_dulwich["not_git_repo"]("Not a git repository")

        git_repository = GitRepository(mock_repo)

        with pytest.raises(RepositoryAccessException) as exc_info:
            git_repository.is_dirty()

        assert "Not a git repository" in str(exc_info.value)

    def test_is_dirty_other_error(self, mock_dulwich):
        """Test is_dirty error handling for other exceptions."""
        mock_repo = Mock()
        mock_repo.path = "/test/repo"

        mock_dulwich["porcelain"].status.side_effect = Exception("Permission denied")

        git_repository = GitRepository(mock_repo)

        with pytest.raises(RepositoryAccessException) as exc_info:
            git_repository.is_dirty()

        assert "Error checking repository status" in str(exc_info.value)
