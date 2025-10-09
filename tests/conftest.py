import pytest
import tempfile
import shutil
from dulwich.repo import Repo
import os
import subprocess
from dulwich.objects import Commit, Tree, Blob
import dulwich.index
import dulwich.porcelain

from dulwich.index import build_index_from_tree

import time
import logging

logging.getLogger("git2df.dulwich_backend").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

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

def _create_dulwich_commit(repo, files_to_add, message, author_name, author_email, timestamp):
    # Write files to the repository working directory
    for filename, content in files_to_add.items():
        file_path = os.path.join(repo.path, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)

    # Add specified files to the index
    if files_to_add:
        dulwich.porcelain.add(repo, list(files_to_add.keys()))

    return repo.do_commit(
        message.encode('utf-8'),
        committer=f"{author_name} <{author_email}>".encode("utf-8"),
        author=f"{author_name} <{author_email}>".encode("utf-8"),
        commit_timestamp=timestamp,
        author_timestamp=timestamp,
    )

@pytest.fixture
def dulwich_repo():
    """
    A pytest fixture that creates a temporary Dulwich repository for testing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "dulwich_test_repo")
        os.makedirs(repo_path, exist_ok=True) # Create the directory before initializing the repo
        repo = Repo.init(repo_path)

        yield repo_path
