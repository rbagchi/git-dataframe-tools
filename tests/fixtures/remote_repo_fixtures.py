import pytest
import tempfile
import os
import subprocess
import logging

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

        # Push all branches to the remote, only if the local repo is not empty
        # Check if there are any commits in the local repo
        result = subprocess.run(["git", "rev-list", "--all", "--count"], cwd=git_repo, capture_output=True, text=True)
        if int(result.stdout.strip()) > 0:
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
        else:
            logging.debug(f"Local repo {git_repo} is empty, skipping push to remote {remote_repo_path}")

        # Return the path to the remote repository
        yield remote_repo_path

        os.chdir(original_cwd)
