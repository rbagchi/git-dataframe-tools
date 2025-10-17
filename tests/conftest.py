import re
import pytest
import tempfile
from dulwich.repo import Repo
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
import time
import pygit2

from dulwich.objects import Commit
import dulwich.index
import dulwich.porcelain


import logging

logging.basicConfig(level=logging.DEBUG)


sample_commits = [
    {
        "author_name": "Test User",
        "author_email": "test@example.com",
        "message": "Initial commit",
        "files": {"file1.txt": "hello world"},
        "commit_date": "2023-01-01T10:00:00Z",
    },
    {
        "author_name": "Test User",
        "author_email": "test@example.com",
        "message": "Second commit",
        "files": {"file2.txt": "another file"},
        "commit_date": "2023-01-01T11:00:00Z",
    },
    {
        "author_name": "Dev User",
        "author_email": "dev@example.com",
        "message": "Third commit by Dev User",
        "files": {"file1.txt": "hello world again"},
        "commit_date": "2023-01-01T12:00:00Z",
    },
]


def extract_code_blocks(markdown_file, language="python"):
    with open(markdown_file, "r") as f:
        content = f.read()
    # Look for code blocks with the specified language
    code_blocks = re.findall(rf"```({language})\n(.*?)\n```", content, re.DOTALL)
    # re.findall returns a list of tuples (language, code_block), we only need the code_block
    return [block for lang, block in code_blocks if lang == language]


def _create_commits(repo_path, commits_data):
    """Helper to create commits in a given repository."""
    for commit_data in commits_data:
        # Set up user for commit
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = commit_data["commit_date"]
        env["GIT_COMMITTER_DATE"] = commit_data["commit_date"]

        subprocess.run(
            ["git", "config", "user.email", commit_data["author_email"]],
            cwd=repo_path,
            check=True,
            env=env
        )
        subprocess.run(
            ["git", "config", "user.name", commit_data["author_name"]],
            cwd=repo_path,
            check=True,
            env=env
        )

        # Create/modify files
        for filename, content in commit_data["files"].items():
            file_path = os.path.join(repo_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
            subprocess.run(["git", "add", filename], cwd=repo_path, check=True, env=env)

        # Commit
        commit_cmd = ["git", "commit", "-m", commit_data["message"]]
        subprocess.run(
            commit_cmd, cwd=repo_path, check=True, env=env
        )
        commit_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True).stdout.strip()
        print(f"DEBUG: CLI Commit hash for '{commit_data['message']}': {commit_hash}")


@pytest.fixture
def git_repo(request):
    """
    A pytest fixture that creates a temporary Git repository for testing.
    Can be pre-populated with commits using `request.param`.
    The `request.param` should be a list of commit data dictionaries.
    Each dictionary can optionally include a 'commit_date' field (datetime object).
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path, exist_ok=True)
        try:
            os.chdir(repo_path)

            # Initialize git repo using git init
            subprocess.run(["git", "init"], cwd=repo_path, check=True)

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

            if hasattr(request, "param") and isinstance(request.param, list):
                # Create an empty initial commit if there are subsequent commits, to establish a HEAD
                if request.param:
                    initial_commit_date = "2023-01-01T09:00:00Z"
                    env = os.environ.copy()
                    env["GIT_AUTHOR_DATE"] = initial_commit_date
                    env["GIT_COMMITTER_DATE"] = initial_commit_date
                    subprocess.run(["git", "commit", "--allow-empty", "-m", "Empty initial commit"], cwd=repo_path, check=True, env=env)
                    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True)
                _create_commits(repo_path, request.param)
            else:
                # Create a default initial commit if no params are passed
                initial_commit_date = "2023-01-01T09:00:00Z"
                env = os.environ.copy()
                env["GIT_AUTHOR_DATE"] = initial_commit_date
                env["GIT_COMMITTER_DATE"] = initial_commit_date
                subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=repo_path, check=True, env=env)
                subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True)

            yield repo_path
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def pygit2_repo(request):
    """
    A pytest fixture that creates a temporary Git repository for testing using pygit2.
    Can be pre-populated with commits using `request.param`.
    The `request.param` should be a list of commit data dictionaries.
    Each dictionary can optionally include a 'commit_date' field (datetime object).
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path, exist_ok=True)
        try:
            os.chdir(repo_path)

            # Initialize pygit2 repository
            repo = pygit2.init_repository(repo_path)

            # Set up default user
            author_name = "Default User"
            author_email = "default@example.com"

            # Initial commit
            initial_file_path = Path(repo_path) / "initial_file.txt"
            initial_file_path.write_text("initial content")
            repo.index.add("initial_file.txt")
            repo.index.write()
            tree = repo.index.write_tree()

            initial_commit_date = "2023-01-01T09:00:00Z"
            initial_commit_timestamp = int(datetime.fromisoformat(initial_commit_date.replace('Z', '+00:00')).timestamp())
            initial_author = pygit2.Signature(author_name, author_email, initial_commit_timestamp, 0)
            initial_committer = pygit2.Signature(author_name, author_email, initial_commit_timestamp, 0)

            initial_commit_oid = repo.create_commit(
                "HEAD", # Commit to HEAD first
                initial_author,
                initial_committer,
                "Initial commit",
                tree,
                [],
            )
            # Create 'main' branch and set HEAD to it
            repo.create_branch("main", repo.get(initial_commit_oid))
            repo.head.set_target(repo.lookup_reference("refs/heads/main").target)

            # Process parameterized commits
            if hasattr(request, "param") and isinstance(request.param, list):
                for commit_data in request.param:
                    # Set up user for commit
                    current_author_name = commit_data.get("author_name", author_name)
                    current_author_email = commit_data.get("author_email", author_email)
                    
                    # Ensure commit_timestamp is derived from fixed commit_date
                    commit_date_obj = datetime.fromisoformat(commit_data["commit_date"].replace('Z', '+00:00'))
                    commit_timestamp = int(commit_date_obj.timestamp())

                    current_author = pygit2.Signature(current_author_name, current_author_email, commit_timestamp, 0)
                    current_committer = pygit2.Signature(current_author_name, current_author_email, commit_timestamp, 0)

                    # Create/modify files
                    for filename, content in commit_data["files"].items():
                        file_path = Path(repo_path) / filename
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(content)
                        repo.index.add(str(filename))

                    # Handle file deletions
                    if "delete_files" in commit_data:
                        for filename in commit_data["delete_files"]:
                            file_path = Path(repo_path) / filename
                            if file_path.exists():
                                file_path.unlink()
                            repo.index.remove(str(filename))

                    # Handle file renames
                    if "rename_files" in commit_data:
                        for old_name, new_name in commit_data["rename_files"]:
                            old_file_path = Path(repo_path) / old_name
                            new_file_path = Path(repo_path) / new_name
                            
                            # Remove old file from index and filesystem
                            if old_file_path.exists():
                                old_file_path.unlink()
                            repo.index.remove(str(old_name))

                            # Add new file to index and filesystem (content should be in commit_data["files"])
                            # Ensure the new file content is already handled by the 'files' loop
                            # If not, we need to read the content from the old file before deleting it
                            # For now, assume new file content is provided in 'files' if it's a rename with content change
                            # Or, if it's a pure rename, the content should be the same as the old file
                            # For this test, we assume the content is passed in 'files' for the new_name
                            if new_name not in commit_data["files"]:
                                # This case should ideally not happen if 'files' is correctly populated for renames
                                # But as a fallback, if new_name is not in 'files', we'll just add it to the index
                                # assuming its content was already written by the 'files' loop (which it won't be if it's a pure rename)
                                # This needs careful handling. For now, let's assume 'files' contains the new_name with its content.
                                pass # The 'files' loop above should handle creating the new file
                            repo.index.add(str(new_name))

                    repo.index.write()
                    tree = repo.index.write_tree()

                    # Create commit
                    parent_commit_oid = repo.head.target
                    repo.create_commit(
                        "refs/heads/main",
                        current_author,
                        current_committer,
                        commit_data["message"],
                        tree,
                        [parent_commit_oid],
                    )
                    repo.head.set_target(repo.lookup_reference("refs/heads/main").target)

            yield repo_path
        finally:
            os.chdir(original_cwd)


@pytest.fixture
def remote_git_repo(git_repo):
    """A pytest fixture that creates a temporary remote Git repository and pushes commits to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as remote_tmpdir:
        remote_repo_path = os.path.join(remote_tmpdir, "remote_repo.git")
        subprocess.run(["git", "init", "--bare", remote_repo_path], check=True)
        print(f"DEBUG: Contents of bare repo {remote_repo_path}:")
        subprocess.run(["ls", "-F", remote_repo_path], check=True)

        # Change to the local repo directory obtained from git_repo fixture
        os.chdir(git_repo)

        # Add the remote
        subprocess.run(["git", "remote", "add", "origin", remote_repo_path], check=True)

        # Push all branches to the remote
        subprocess.run(["git", "push", "--all", "origin"], check=True)
        # Explicitly set HEAD in the bare repo to main
        subprocess.run(["git", "--git-dir", remote_repo_path, "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        head_content = subprocess.run(["cat", os.path.join(remote_repo_path, "HEAD")], check=True, capture_output=True, text=True).stdout
        logging.debug(f"Content of HEAD in bare repo {remote_repo_path}:\n{head_content}")
         
        branches_output = subprocess.run(["git", "--git-dir", remote_repo_path, "branch", "-a"], check=True, capture_output=True, text=True).stdout
        logging.debug(f"Branches in bare repo {remote_repo_path}:\n{branches_output}")
        log_output = subprocess.run(["git", "--git-dir", remote_repo_path, "log", "--all", "--oneline"], check=True, capture_output=True, text=True).stdout
        logging.debug(f"Log in bare repo {remote_repo_path}:\n{log_output}")
        rev_parse_output = subprocess.run(["git", "--git-dir", remote_repo_path, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout
        logging.debug(f"HEAD (rev-parse) in bare repo {remote_repo_path}:\n{rev_parse_output}")
         
        # Return the path to the remote repository
        yield remote_repo_path

        os.chdir(original_cwd)
