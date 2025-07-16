from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omnitool.builtin_plugins.git.plugin import checkout_operation, definition, load_context
from omnitool.builtin_plugins.git.repository import GitRepository, RepositoryAccessException
from omnitool.plugin.api.context import Context, Location, Resource


class TestContextLoader:
    """Test cases for the git plugin context loader."""

    def test_load_context_success(self, mock_dulwich):
        """Test successful context loading."""
        # Setup - mock a valid git repository
        mock_repo_instance = Mock()
        mock_repo_instance.path = "/test/repo"
        mock_dulwich["repo"].return_value = mock_repo_instance

        # Create context
        repo_path = Path("/test/repo")
        location = Location(path=repo_path)
        resource = Resource(name="test_repo", location=location)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Mock path existence and directory check
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=True):
            # Execute
            load_context(context)

            # Verify
            assert isinstance(resource.data, GitRepository)
            assert resource.data.repo == mock_repo_instance
            assert resource.data.path == repo_path
            mock_dulwich["repo"].assert_called_once_with(str(repo_path))

    def test_load_context_path_not_exists(self):
        """Test error when path doesn't exist."""
        # Create context
        repo_path = Path("/test/repo")
        location = Location(path=repo_path)
        resource = Resource(name="test_repo", location=location)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Setup - mock path doesn't exist
        with patch.object(Path, "exists", return_value=False):
            # Execute and verify
            with pytest.raises(RepositoryAccessException) as exc_info:
                load_context(context)

            assert "Path does not exist" in str(exc_info.value)

    def test_load_context_path_not_directory(self):
        """Test error when path is not a directory."""
        # Create context
        repo_path = Path("/test/repo")
        location = Location(path=repo_path)
        resource = Resource(name="test_repo", location=location)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Setup - path exists but is not a directory
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=False):
            # Execute and verify
            with pytest.raises(RepositoryAccessException) as exc_info:
                load_context(context)

            assert "Path is not a directory" in str(exc_info.value)

    def test_load_context_not_git_repository(self, mock_dulwich):
        """Test error when path is not a git repository."""
        # Setup - path exists and is directory but not a git repo
        mock_dulwich["repo"].side_effect = mock_dulwich["not_git_repo"]("Not a git repository")

        # Create context
        repo_path = Path("/test/repo")
        location = Location(path=repo_path)
        resource = Resource(name="test_repo", location=location)
        context = Context(name="test_context", resources={"test_repo": resource})

        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=True):
            # Execute and verify
            with pytest.raises(RepositoryAccessException) as exc_info:
                load_context(context)

            assert "Not a git repository" in str(exc_info.value)

    def test_load_context_multiple_resources(self, mock_dulwich):
        """Test loading context with multiple repositories."""
        # Setup
        mock_repo1 = Mock()
        mock_repo1.path = "/test/repo1"
        mock_repo2 = Mock()
        mock_repo2.path = "/test/repo2"

        # Mock Repo constructor to return different instances
        def mock_repo_constructor(path_str):
            if "repo1" in path_str:
                return mock_repo1
            else:
                return mock_repo2

        mock_dulwich["repo"].side_effect = mock_repo_constructor

        # Create context with multiple repositories
        repo1_path = Path("/test/repo1")
        repo2_path = Path("/test/repo2")

        location1 = Location(path=repo1_path)
        location2 = Location(path=repo2_path)

        resource1 = Resource(name="repo1", location=location1)
        resource2 = Resource(name="repo2", location=location2)

        context = Context(name="multi_repo_context", resources={"repo1": resource1, "repo2": resource2})

        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=True):
            # Execute
            load_context(context)

            # Verify both repositories were initialized
            assert isinstance(resource1.data, GitRepository)
            assert isinstance(resource2.data, GitRepository)
            assert resource1.data.repo == mock_repo1
            assert resource2.data.repo == mock_repo2

    def test_load_context_unexpected_error(self, mock_dulwich):
        """Test handling of unexpected errors during context loading."""
        # Setup - unexpected error during git repo validation
        mock_dulwich["repo"].side_effect = Exception("Unexpected error")

        # Create context
        repo_path = Path("/test/repo")
        location = Location(path=repo_path)
        resource = Resource(name="test_repo", location=location)
        context = Context(name="test_context", resources={"test_repo": resource})

        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=True):
            # Execute and verify
            with pytest.raises(RepositoryAccessException) as exc_info:
                load_context(context)

            assert "Failed to initialize test_repo" in str(exc_info.value)


class TestPluginDefinition:
    """Test cases for the git plugin definition."""

    def test_plugin_definition_properties(self):
        """Test plugin definition has correct properties."""
        assert definition.root_operation_name == "git"
        assert definition.resource_data_type == GitRepository
        assert definition.context_loader_function is not None

    def test_plugin_definition_has_operations(self):
        """Test plugin definition has checkout operation."""
        # The operations are registered via decorators, check they exist
        assert len(definition.operations) > 0

        # Find the checkout operation
        checkout_op = None
        for op in definition.operations:
            if hasattr(op, "__name__") and "checkout" in op.__name__:
                checkout_op = op
                break

        assert checkout_op is not None


class TestCheckoutOperationIntegration:
    """Test cases for the checkout operation integration."""

    @pytest.mark.asyncio
    async def test_checkout_operation_delegates_to_checkout(self, mock_dulwich):
        """Test that checkout_operation correctly delegates to the checkout function."""
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
        repo_path = Path("/test/repo")
        location = Location(path=repo_path)
        resource = Resource(name="test_repo", location=location, data=git_repo)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        await checkout_operation("develop", context, create=False)

        # Verify the underlying checkout function was called
        mock_dulwich["porcelain"].reset.assert_called()

    @pytest.mark.asyncio
    async def test_checkout_operation_with_create_flag(self, mock_dulwich):
        """Test checkout operation with create flag."""
        # Setup mock repo
        mock_repo_instance = Mock()
        mock_repo_instance.refs = {
            b"HEAD": b"commit_hash_main",
            b"refs/heads/main": b"commit_hash_main",
        }
        mock_repo_instance.path = "/test/repo"

        # Setup GitRepository and context
        git_repo = GitRepository(mock_repo_instance)
        repo_path = Path("/test/repo")
        location = Location(path=repo_path)
        resource = Resource(name="test_repo", location=location, data=git_repo)
        context = Context(name="test_context", resources={"test_repo": resource})

        # Mock porcelain.reset
        mock_dulwich["porcelain"].reset = Mock()

        # Execute
        await checkout_operation("new-feature", context, create=True)

        # Verify
        mock_dulwich["porcelain"].reset.assert_called()
