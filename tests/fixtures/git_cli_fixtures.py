import pytest
import tempfile
import os
import subprocess

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
