import pytest
import subprocess
import os
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch

import re


from git_scoreboard.config_models import GitAnalysisConfig
from git_scoreboard.git_utils import get_git_data_from_config



@pytest.fixture(scope="function")
def temp_git_repo(tmp_path):
    """Fixture to create a temporary git repository for integration tests."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)

    # Set up a dummy user for commits
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)

    # Create some commits
    (repo_path / "file1.txt").write_text("hello world")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

    (repo_path / "file2.txt").write_text("another file")
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Second commit"], cwd=repo_path, check=True)

    # Simulate a different author
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev User"], cwd=repo_path, check=True)

    (repo_path / "file1.txt").write_text("hello world again")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Third commit by Dev User"], cwd=repo_path, check=True)

    yield repo_path

    # Teardown: shutil.rmtree(repo_path) is handled by tmp_path fixture

@pytest.fixture(scope="function")
def temp_git_repo_with_remote(tmp_path):
    """Fixture to create a temporary git repository with a bare remote for integration tests."""
    print(f"DEBUG: tmp_path: {tmp_path}")
    remote_path = tmp_path / "remote.git"
    repo_path = tmp_path / "test_repo"
    print(f"DEBUG: remote_path: {remote_path}, repo_path: {repo_path}")

    # Create bare remote repository
    subprocess.run(["git", "init", "--bare", str(remote_path)], check=True)
    print("DEBUG: Remote repo initialized.")

    # Initialize local git repo
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    print("DEBUG: Local repo initialized.")

    # Set up a dummy user for commits
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    print("DEBUG: Test User configured.")

    # Add remote
    subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True)
    print("DEBUG: Remote added.")

    # Create some commits on master and push to remote
    (repo_path / "file1.txt").write_text("hello world")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "-u", "origin", "master"], cwd=repo_path, check=True)
    print("DEBUG: Initial commit pushed.")

    (repo_path / "file2.txt").write_text("another file")
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Second commit"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)
    print("DEBUG: Second commit pushed.")

    # Simulate a different author
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev User"], cwd=repo_path, check=True)
    print("DEBUG: Dev User configured.")

    (repo_path / "file1.txt").write_text("hello world again")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Third commit by Dev User"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)
    print("DEBUG: Third commit pushed.")

    # Commit for include/exclude path testing
    src_dir = repo_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "feature.js").write_text("console.log('feature');")
    subprocess.run(["git", "add", "src/feature.js"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add feature.js"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)
    print("DEBUG: Feature commit pushed.")

    docs_dir = repo_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "README.md").write_text("Documentation update")
    subprocess.run(["git", "add", "docs/README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Update docs"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)
    print("DEBUG: Docs commit pushed.")

    # Teardown: shutil.rmtree(tmp_path) handles cleanup
    yield repo_path

# Test check_git_repo
def test_check_git_repo_integration(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig()
        assert config._check_git_repo(repo_path=temp_git_repo_with_remote) is True
    finally:
        os.chdir(original_cwd)

def test_check_git_repo_not_a_repo(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        config = GitAnalysisConfig()
        assert config._check_git_repo() is False
    finally:
        os.chdir(original_cwd)

# Test GitAnalysisConfig._get_current_git_user
def test_get_current_git_user_integration(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(use_current_user=True)
        # The last user configured in the fixture is 'Dev User'
        assert config.current_user_name == "Dev User"
        assert config.current_user_email == "dev@example.com"
    finally:
        os.chdir(original_cwd)





# Test GitAnalysisConfig.get_git_log_data
def test_get_git_log_data_integration_default(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31")
        git_data_df = get_git_data_from_config(config, repo_path=temp_git_repo_with_remote)

        # Check for presence of expected authors and total number of commits
        assert not git_data_df.empty
        assert "Test User" in git_data_df['author_name'].values
        assert "Dev User" in git_data_df['author_name'].values
        assert git_data_df['num_commits'].sum() == 5 # 5 commits in the fixture

    finally:
        os.chdir(original_cwd)

def test_get_git_log_data_integration_merged_only(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31", merged_only=True)
        git_data_df = get_git_data_from_config(config, repo_path=temp_git_repo_with_remote)

        # Expect no commits as the fixture does not create merge commits
        assert git_data_df.empty
    finally:
        os.chdir(original_cwd)

def test_get_git_log_data_integration_include_paths(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31", include_paths=["src/"])
        git_data_df = get_git_data_from_config(config, repo_path=temp_git_repo_with_remote)

        assert not git_data_df.empty
        assert "Dev User" in git_data_df['author_name'].values # 'Add feature.js' commit is by Dev User
        assert "Test User" not in git_data_df['author_name'].values # Test User has no commits in src/ after Dev User config
        assert git_data_df['num_commits'].sum() == 1 # Only 'Add feature.js' commit

    finally:
        os.chdir(original_cwd)

def test_get_git_log_data_integration_exclude_paths(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31", exclude_paths=["docs/"])
        git_data_df = get_git_data_from_config(config, repo_path=temp_git_repo_with_remote)

        assert not git_data_df.empty
        assert "Test User" in git_data_df['author_name'].values
        assert "Dev User" in git_data_df['author_name'].values
        assert git_data_df['num_commits'].sum() == 4 # 5 total commits, 1 in docs excluded

        # Ensure excluded commit's author is still present if they have other commits
        # The 'Update docs' commit is by 'Test User', who also has other commits.
        # So 'Test User' should still be present, but with fewer commits.
        test_user_commits = git_data_df[git_data_df['author_name'] == "Test User"]['num_commits'].sum()
        assert test_user_commits == 2 # Initial, Second (Add feature.js is by Dev User, Update docs excluded)

    finally:
        os.chdir(original_cwd)
