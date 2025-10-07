import pytest
import tempfile
import shutil
from dulwich.repo import Repo
import os
import subprocess

def _create_commits(repo_path, commits_data):
    """Helper to create commits in a given repository."""
    for commit_data in commits_data:
        # Set up user for commit
        subprocess.run(
            ["git", "config", "user.email", commit_data["author_email"]],
            cwd=repo_path,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", commit_data["author_name"]],
            cwd=repo_path,
            check=True,
        )

        # Create/modify files
        for filename, content in commit_data["files"].items():
            file_path = os.path.join(repo_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
            subprocess.run(["git", "add", filename], cwd=repo_path, check=True)

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_data["message"]], cwd=repo_path, check=True
        )

@pytest.fixture
def git_repo(request):
    """
    A pytest fixture that creates a temporary Git repository for testing.
    Can be pre-populated with commits using `request.param`.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path, exist_ok=True) # Create the directory before initializing the repo
        Repo.init(repo_path)

        # Set up a default dummy user for initial git config
        subprocess.run(
            ["git", "config", "user.email", "default@example.com"], cwd=repo_path, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Default User"], cwd=repo_path, check=True
        )

        if hasattr(request, "param") and request.param:
            _create_commits(repo_path, request.param)

        yield repo_path