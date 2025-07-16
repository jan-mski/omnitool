
import pytest
from dulwich.repo import Repo


@pytest.fixture
def git_repo(tmpdir) -> Repo:
    repo_path = tmpdir.mkdir("repo")
    repo = Repo.init(str(repo_path))
    
    # Add an initial commit
    config = repo.get_config()
    config.set(b"user", b"name", b"Test User")
    config.set(b"user", b"email", b"test@example.com")
    config.write_to_path()
    
    repo.do_commit(b"Initial commit", committer=b"Test User <test@example.com>")
    repo.refs.set_symbolic_ref(b'HEAD', b'refs/heads/master')
    
    return repo
