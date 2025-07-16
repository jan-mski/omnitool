from pathlib import Path
from unittest.mock import Mock

import pytest

from omnitool.builtin_plugins.git.operations import _checkout_single_repository, _execute_checkout_async, checkout
from omnitool.builtin_plugins.git.repository import GitRepository
from omnitool.plugin.api.context import Context, Location, Resource


class TestCheckoutOperation:
    """Test cases for checkout operation."""

    @pytest.mark.asyncio
    async def test_checkout_existing_branch(self, mock_dulwich):
        """Test switching to existing branch."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo_instance.path = "/test/repo"

        # Setup GitRepository and context
        git_repo = GitRepository(mock_repo_instance)
        location = Location(path=Path("/test/repo"))
        resource = Resource(name="test_repo", location=location, data=git_repo)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        await checkout("develop", create=False, context=context)

        # Verify reset was called
        mock_dulwich["porcelain"].reset.assert_called()

    @pytest.mark.asyncio
    async def test_checkout_create_branch(self, mock_dulwich):
        """Test creating new branch."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
        }
        mock_repo_instance.path = "/test/repo"

        # Setup GitRepository and context
        git_repo = GitRepository(mock_repo_instance)
        location = Location(path=Path("/test/repo"))
        resource = Resource(name="test_repo", location=location, data=git_repo)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        await checkout("new-feature", create=True, context=context)

        # Verify reset was called
        mock_dulwich["porcelain"].reset.assert_called()

    @pytest.mark.asyncio
    async def test_checkout_nonexistent_branch_fails(self, mock_dulwich):
        """Test error when branch doesn't exist."""
        # Setup mock repo without the requested branch
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
        }
        mock_repo_instance.path = "/test/repo"

        # Setup GitRepository and context
        git_repo = GitRepository(mock_repo_instance)
        location = Location(path=Path("/test/repo"))
        resource = Resource(name="test_repo", location=location, data=git_repo)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Execute - should not raise exception at checkout level, but log errors
        await checkout("nonexistent", create=False, context=context)

        # The operation should complete without raising exception
        # Errors are logged and handled internally

    @pytest.mark.asyncio
    async def test_checkout_branch_already_exists_fails(self, mock_dulwich):
        """Test error when trying to create existing branch."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo_instance.path = "/test/repo"

        # Setup GitRepository and context
        git_repo = GitRepository(mock_repo_instance)
        location = Location(path=Path("/test/repo"))
        resource = Resource(name="test_repo", location=location, data=git_repo)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Execute - should not raise exception at checkout level
        await checkout("main", create=True, context=context)

        # The operation should complete, errors are handled internally

    @pytest.mark.asyncio
    async def test_checkout_no_context(self, caplog):
        """Test checkout with no context."""
        await checkout("main", create=False, context=None)

        assert "No repositories found in context" in caplog.text

    @pytest.mark.asyncio
    async def test_checkout_empty_context(self, caplog):
        """Test checkout with empty context."""
        empty_context = Context(name="empty", resources={})

        await checkout("main", create=False, context=empty_context)

        assert "No repositories found in context" in caplog.text

    @pytest.mark.asyncio
    async def test_checkout_no_git_repositories(self, caplog):
        """Test checkout with context containing non-GitRepository resources."""
        # Create context with resource that doesn't have GitRepository data
        location = Location(path=Path("/test/path"))
        resource = Resource(name="test_resource", location=location, data=None)
        context = Context(name="test", resources={"test_resource": resource})

        await checkout("main", create=False, context=context)

        assert "No GitRepository resources found in context" in caplog.text

    @pytest.mark.asyncio
    async def test_multiple_repositories_async(self, mock_dulwich):
        """Test async operation on multiple repositories."""
        # Setup mock repos
        mock_repo1 = Mock()
        mock_repo1.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo1.path = "/test/repo1"

        mock_repo2 = Mock()
        mock_repo2.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo2.path = "/test/repo2"

        # Setup GitRepositories and context
        git_repo1 = GitRepository(mock_repo1)
        git_repo2 = GitRepository(mock_repo2)

        location1 = Location(path=Path("/test/repo1"))
        location2 = Location(path=Path("/test/repo2"))

        resource1 = Resource(name="repo1", location=location1, data=git_repo1)
        resource2 = Resource(name="repo2", location=location2, data=git_repo2)

        context = Context(name="multi_repo_context", resources={"repo1": resource1, "repo2": resource2})

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        await checkout("develop", create=False, context=context)

        # Verify reset was called for both repositories
        assert mock_dulwich["porcelain"].reset.call_count == 2


class TestExecuteCheckoutAsync:
    """Test cases for async checkout execution."""

    @pytest.mark.asyncio
    async def test_execute_checkout_async_success(self, mock_dulwich):
        """Test successful async execution."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo_instance.path = "/test/repo"

        repositories = [GitRepository(mock_repo_instance)]

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        results = await _execute_checkout_async(repositories, "develop", False)

        # Verify
        assert len(results) == 1
        success, message = results[0]
        assert success is True
        assert "Successfully checked out branch 'develop'" in message

    @pytest.mark.asyncio
    async def test_execute_checkout_async_partial_failure(self, mock_dulwich):
        """Test async execution with partial failures."""
        # Setup - one successful repo, one failing repo
        mock_repo1 = Mock()
        mock_repo1.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo1.path = "/test/repo1"

        # Second repo will fail - simulate refs access raising exception
        mock_repo2 = Mock()
        mock_repo2.path = "/test/repo2"
        mock_repo2.refs.__contains__.side_effect = mock_dulwich["not_git_repo"]("Not a git repository")

        repositories = [GitRepository(mock_repo1), GitRepository(mock_repo2)]

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        results = await _execute_checkout_async(repositories, "develop", False)

        # Verify
        assert len(results) == 2

        # First repo should succeed
        success1, message1 = results[0]
        assert success1 is True

        # Second repo should fail
        success2, message2 = results[1]
        assert success2 is False
        assert "Not a git repository" in message2


class TestCheckoutSingleRepository:
    """Test cases for single repository checkout operations."""

    def test_checkout_existing_branch_success(self, mock_dulwich):
        """Test successful checkout of existing branch."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
            b"refs/heads/develop": b"commit_hash_develop",
        }
        mock_repo_instance.path = "/test/repo"

        git_repo = GitRepository(mock_repo_instance)

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        success, message = _checkout_single_repository(git_repo, "develop", False)

        # Verify
        assert success is True
        assert "Successfully checked out branch 'develop'" in message
        mock_dulwich["porcelain"].reset.assert_called_once()

    def test_checkout_create_branch_success(self, mock_dulwich):
        """Test successful creation of new branch."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
        }
        mock_repo_instance.path = "/test/repo"

        git_repo = GitRepository(mock_repo_instance)

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        success, message = _checkout_single_repository(git_repo, "new-feature", True)

        # Verify
        assert success is True
        assert "Successfully checked out branch 'new-feature'" in message
        mock_dulwich["porcelain"].reset.assert_called_once()

    def test_checkout_nonexistent_branch_error(self):
        """Test error when checking out non-existent branch."""
        # Setup mock repo without the requested branch
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
        }
        mock_repo_instance.path = "/test/repo"

        git_repo = GitRepository(mock_repo_instance)

        # Execute
        success, message = _checkout_single_repository(git_repo, "nonexistent", False)

        # Verify
        assert success is False
        assert "Branch 'nonexistent' does not exist" in message

    def test_checkout_create_existing_branch_error(self):
        """Test error when trying to create existing branch."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
        }
        mock_repo_instance.path = "/test/repo"

        git_repo = GitRepository(mock_repo_instance)

        # Execute
        success, message = _checkout_single_repository(git_repo, "main", True)

        # Verify
        assert success is False
        assert "A branch named 'main' already exists" in message

    def test_checkout_not_git_repository_error(self, mock_dulwich):
        """Test error when path is not a git repository."""
        # Setup mock repo that raises NotGitRepository
        mock_repo_instance = Mock()
        mock_repo_instance.path = "/test/repo"
        mock_repo_instance.refs.__contains__.side_effect = mock_dulwich["not_git_repo"]("Not a git repository")

        git_repo = GitRepository(mock_repo_instance)

        # Execute
        success, message = _checkout_single_repository(git_repo, "main", False)

        # Verify
        assert success is False
        assert "Not a git repository: /test/repo" in message

    def test_checkout_permission_error(self):
        """Test error when permission denied."""
        # Setup mock repo that raises PermissionError
        mock_repo_instance = Mock()
        mock_repo_instance.path = "/test/repo"
        mock_repo_instance.refs.__contains__.side_effect = PermissionError("Permission denied")

        git_repo = GitRepository(mock_repo_instance)

        # Execute
        success, message = _checkout_single_repository(git_repo, "main", False)

        # Verify
        assert success is False
        assert "Permission denied: /test/repo" in message

    def test_checkout_unexpected_error(self):
        """Test handling of unexpected errors."""
        # Setup mock repo that raises unexpected error
        mock_repo_instance = Mock()
        mock_repo_instance.path = "/test/repo"
        mock_repo_instance.refs.__contains__.side_effect = Exception("Unexpected error")

        git_repo = GitRepository(mock_repo_instance)

        # Execute
        success, message = _checkout_single_repository(git_repo, "main", False)

        # Verify
        assert success is False
        assert "Unexpected error in /test/repo" in message
