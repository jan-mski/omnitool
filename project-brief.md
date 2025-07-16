# Git Plugin Specification for Omnitool

## Overview

This document specifies the requirements for implementing a git repository management plugin for Omnitool. The plugin will provide branch management capabilities (checkout and creation) for git repositories discovered and managed by the Omnitool framework.

## Architecture Overview

The plugin follows Omnitool's plugin architecture where:
- Repositories are represented as `ResourceData` objects
- Discovery and state management is handled by Omnitool
- The plugin implements the data model and operation functions
- Operations can work on multiple repositories asynchronously

## Core Requirements

### 1. Resource Data Model

The `GitRepository` class extends `ResourceData` and contains:

**Stored Field:**
- `_repo: Repo` - The git repository object (from the dulwich library)

**Methods:**
- `get_current_branch() -> str` - Returns the currently checked out branch name
- `get_branches() -> List[str]` - Returns a list of all local branches
- `get_remote_branches() -> List[str]` - Returns a list of all remote branches
- `is_dirty() -> bool` - Returns whether the repository has uncommitted changes

All methods must catch all exceptions and re-raise them as `RepositoryAccessException` (a new class defined for this purpose).

### 2. Operations

#### checkout(branch: str, create: bool = False, context: Context) -> None

Single operation that handles both branch switching and creation, mirroring git's interface.

**Parameters:**
- `branch`: Name of the branch to checkout
- `create`: If True, create the branch (equivalent to `git checkout -b`)
- `context`: Omnitool context containing GitRepository resources

**Behavior:**
- When `create=False`: Switch to existing branch
- When `create=True`: Create new branch from current HEAD and switch to it
- Preserve uncommitted changes during checkout (same as git)
- Operate on all repositories in context asynchronously

**Error Handling:**
- Branch doesn't exist (when create=False): Raise `RepositoryAccessException` with message "Branch 'branch_name' does not exist"
- Branch already exists (when create=True): Raise `RepositoryAccessException` with message "A branch named 'branch_name' already exists"
- Other errors: Raise with appropriate user-friendly messages

### 3. Context Loader

The context loader is a function that follows the `ContextLoaderProtocol` and should be decorated with the appropriate decorator in `PluginDefinition`.
In the context of this plugin, the context loader should:
- Initialize GitRepository objects from the context
- Validate that paths point to valid git repositories
- Set up any necessary state for the repositories

## Implementation Details

### Dependencies

**Required Library:** dulwich (pure Python git implementation)
- Installed as optional dependency: `pip install omnitool[git-plugin]`
- Add to `pyproject.toml` under `[project.optional-dependencies]`

### Asynchronous Execution

- Use `asyncio` with `ThreadPoolExecutor` for parallel operations
- Each repository operation runs in a separate thread
- Log successes and failures as a simple list after completion

### Logging

**Info Level:**
- Operation start: "Starting checkout operation on N repositories"
- Operation completion: "Checkout completed: N succeeded, M failed"
- Individual success: "Repository /path/to/repo: Checked out branch 'branch_name'"
- Individual success (create): "Repository /path/to/repo: Created and checked out branch 'branch_name'"

**Debug Level:**
- Detailed dulwich API calls
- Repository state before/after operations
- Full error traces

### Error Messages

User-friendly error messages for common scenarios:
- "Branch 'branch_name' does not exist"
- "A branch named 'branch_name' already exists"
- "Not a git repository: /path/to/dir"
- "Permission denied: /path/to/repo"

## Testing Strategy

### Unit Tests with Mocked Operations

Tests should mock dulwich API calls and verify:

1. **Correct Dulwich API Usage**
   - Proper repository initialization
   - Correct branch operations sequence
   - Appropriate error handling for dulwich exceptions

2. **Edge Cases**
   - Non-existent branches
   - Existing branches when creating
   - Invalid repository paths
   - Permission errors
   - Corrupted repositories

3. **Async Behavior**
   - Multiple repositories processed in parallel
   - Partial failures don't affect other repos
   - Proper aggregation of results
   - Thread safety

### Test Structure

```python
# Example test structure
def test_checkout_existing_branch(self, mock_dulwich):
    # Test switching to existing branch

def test_checkout_create_branch(self, mock_dulwich):
    # Test creating new branch

def test_checkout_nonexistent_branch_fails(self, mock_dulwich):
    # Test error when branch doesn't exist

def test_multiple_repositories_async(self, mock_dulwich):
    # Test async operation on multiple repos

def test_gitrepository_properties(self, mock_dulwich):
    # Test dynamic property computation
```

## File Structure

```
omnitool/builtin_plugins/git/
├── __init__.py
├── plugin.py          # Main plugin definition
├── repository.py      # GitRepository class implementation
├── operations.py      # Checkout operation implementation

tests/builtin_plugins/git/
├── __init__.py
├── test_repository.py
├── test_operations.py
└── conftest.py       # Fixtures for git tests
```

## Example Usage

```python
# After Omnitool loads the plugin and discovers repositories
# User runs: omnitool git checkout main
# Or: omnitool git checkout -b feature/new-feature

# The operation receives a context with GitRepository resources
# and performs the checkout on all repositories
```

## Future Considerations

While not in initial scope, the architecture should not prevent future additions:
- Additional git operations (status, commit, push, pull)
- Remote repository operations
- Stash management
- Merge conflict resolution

## Development Checklist

1. [ ] Update `pyproject.toml` with dulwich optional dependency
2. [ ] Implement `GitRepository` class with dynamic properties
3. [ ] Implement `checkout` operation with async support
4. [ ] Implement context loader
5. [ ] Create comprehensive unit tests
6. [ ] Add logging at appropriate levels
7. [ ] Document error messages and exceptions
8. [ ] Verify async behavior with multiple repositories
9. [ ] Update plugin module exports
10. [ ] Run full test suite

## Acceptance Criteria

- [ ] Can checkout existing branches on single repository
- [ ] Can create and checkout new branches on single repository  
- [ ] Handles multiple repositories asynchronously
- [ ] Provides clear error messages for common failures
- [ ] All unit tests pass with 100% coverage of critical paths
- [ ] Logging provides useful information without being verbose
- [ ] Installation with optional dependency works correctly 