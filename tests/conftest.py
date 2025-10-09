import pytest
import tempfile
import shutil
from dulwich.repo import Repo
import os
import subprocess
from pathlib import Path
import git
from dulwich.objects import Commit, Tree, Blob
import dulwich.index
import dulwich.porcelain

from dulwich.index import build_index_from_tree

import time
import logging

logging.getLogger("git2df.dulwich_backend").setLevel(logging.DEBUG)
import re

logger = logging.getLogger(__name__)

sample_commits = [
    {
        "author_name": "Test User",
        "author_email": "test@example.com",
        "message": "Initial commit",
        "files": {"file1.txt": "hello world"},
    },
    {
        "author_name": "Test User",
        "author_email": "test@example.com",
        "message": "Second commit",
        "files": {"file2.txt": "another file"},
    },
    {
        "author_name": "Dev User",
        "author_email": "dev@example.com",
        "message": "Third commit by Dev User",
        "files": {"file1.txt": "hello world again"},
    },
]

def extract_code_blocks(markdown_file, language="python"):
    with open(markdown_file, 'r') as f:
        content = f.read()
    # Look for code blocks with the specified language
    code_blocks = re.findall(rf"```({language})\n(.*?)\n```", content, re.DOTALL)
    # re.findall returns a list of tuples (language, code_block), we only need the code_block
    return [block for lang, block in code_blocks if lang == language]

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
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path, exist_ok=True)  # Create the directory before initializing the repo
        try:
            os.chdir(repo_path)  # Change to the repo directory
            Repo.init(repo_path)
            repo = git.Repo(repo_path)
            # Initial commit
            (Path(repo_path) / "initial_file.txt").write_text("initial content")
            repo.index.add(["initial_file.txt"])
            initial_commit = repo.index.commit("Initial commit")

            repo.head.reference = repo.create_head(
                "main", initial_commit
            )  # Create and checkout main branch

            # Set up a default dummy user for initial git config
            subprocess.run(
                ["git", "config", "user.email", "default@example.com"],
                cwd=repo_path,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Default User"],
                cwd=repo_path,
                check=True,
            )

            if hasattr(request, "param") and request.param:
                _create_commits(repo_path, request.param)

            yield repo_path
        finally:
            os.chdir(original_cwd)

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

    # Manually create commit object
    commit = Commit()
    commit.author = f"{author_name} <{author_email}>".encode("utf-8")
    commit.committer = commit.author
    commit.commit_time = timestamp
    commit.author_time = timestamp
    commit.author_timezone = 0
    commit.commit_timezone = 0
    commit.encoding = b"UTF-8"
    commit.message = message.encode("utf-8")

    try:
        commit.parents = [repo.head()]
    except KeyError:
        commit.parents = []

    # Create a tree from the index and set it to the commit
    index = repo.open_index()
    tree_id = index.commit(repo.object_store)
    commit.tree = tree_id

    repo.object_store.add_object(commit)
    repo.refs[b"refs/heads/main"] = commit.id
    repo.refs[b"HEAD"] = commit.id

    return commit.id

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
