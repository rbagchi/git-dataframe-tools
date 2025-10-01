import pytest
import subprocess
import os
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch

import re


from git_scoreboard.scoreboard import GitAnalysisConfig, check_git_repo

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
    remote_path = tmp_path / "remote.git"
    repo_path = tmp_path / "test_repo"

    # Create bare remote repository
    subprocess.run(["git", "init", "--bare", str(remote_path)], check=True)

    # Initialize local git repo
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)

    # Set up a dummy user for commits
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)

    # Add remote
    subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True)

    # Create some commits on master and push to remote
    (repo_path / "file1.txt").write_text("hello world")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "-u", "origin", "master"], cwd=repo_path, check=True)

    (repo_path / "file2.txt").write_text("another file")
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Second commit"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)

    # Simulate a different author
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev User"], cwd=repo_path, check=True)

    (repo_path / "file1.txt").write_text("hello world again")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Third commit by Dev User"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)

    # Commit for include/exclude path testing
    src_dir = repo_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "feature.js").write_text("console.log('feature');")
    subprocess.run(["git", "add", "src/feature.js"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add feature.js"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)

    docs_dir = repo_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "README.md").write_text("Documentation update")
    subprocess.run(["git", "add", "docs/README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Update docs"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=repo_path, check=True)

    yield repo_path

    # Teardown: shutil.rmtree(tmp_path) handles cleanup

# Test check_git_repo
def test_check_git_repo_integration(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        assert check_git_repo() is True
    finally:
        os.chdir(original_cwd)

def test_check_git_repo_not_a_repo(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        assert check_git_repo() is False
    finally:
        os.chdir(original_cwd)

# Test GitAnalysisConfig._get_current_git_user
def test_get_current_git_user_integration(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig()
        name, email = config._get_current_git_user()
        # The last user configured in the fixture is 'Dev User'
        assert name == "Dev User"
        assert email == "dev@example.com"
    finally:
        os.chdir(original_cwd)

# Test GitAnalysisConfig._get_main_branch
def test_get_main_branch_integration_main(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        # Create a 'main' branch and push it to the remote
        subprocess.run(["git", "checkout", "-b", "main"], cwd=temp_git_repo_with_remote, check=True)
        (temp_git_repo_with_remote / "file3.txt").write_text("file on main")
        subprocess.run(["git", "add", "file3.txt"], cwd=temp_git_repo_with_remote, check=True)
        subprocess.run(["git", "commit", "-m", "Commit on main"], cwd=temp_git_repo_with_remote, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=temp_git_repo_with_remote, check=True)

        config = GitAnalysisConfig()
        assert config._get_main_branch() == "origin/main"
    finally:
        os.chdir(original_cwd)

def test_get_main_branch_integration_master(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        # master branch is already pushed in the fixture
        config = GitAnalysisConfig()
        assert config._get_main_branch() == "origin/master"
    finally:
        os.chdir(original_cwd)

# Test GitAnalysisConfig._estimate_commit_count
def test_estimate_commit_count_integration_default(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31")
        # There are 5 commits in the fixture
        assert config._estimate_commit_count() == 5
    finally:
        os.chdir(original_cwd)

# Test GitAnalysisConfig.get_git_log_data
def test_get_git_log_data_integration_default(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31")
        git_data = config.get_git_log_data()

        # Check for presence of all commit messages and some file paths
        assert "Initial commit" in git_data
        assert "Second commit" in git_data
        assert "Third commit by Dev User" in git_data
        assert "Add feature.js" in git_data
        assert "Update docs" in git_data
        assert "file1.txt" in git_data
        assert "file2.txt" in git_data
        assert "src/feature.js" in git_data
        assert "docs/README.md" in git_data
    finally:
        os.chdir(original_cwd)

def test_get_git_log_data_integration_merged_only(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31", merged_only=True)
        git_data = config.get_git_log_data()

        # All 5 commits are on master and pushed, so they should be present
        assert "Initial commit" in git_data
        assert "Second commit" in git_data
        assert "Third commit by Dev User" in git_data
        assert "Add feature.js" in git_data
        assert "Update docs" in git_data
    finally:
        os.chdir(original_cwd)

def test_get_git_log_data_integration_include_paths(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31", include_paths=["src/"])
        git_data = config.get_git_log_data()

        assert "Add feature.js" in git_data
        assert "src/feature.js" in git_data

        # Ensure other commits/files are NOT present
        assert "Initial commit" not in git_data
        assert "Second commit" not in git_data
        assert "Third commit by Dev User" not in git_data
        assert "Update docs" not in git_data
        assert "file1.txt" not in git_data
        assert "file2.txt" not in git_data
        assert "docs/README.md" not in git_data
    finally:
        os.chdir(original_cwd)

def test_get_git_log_data_integration_exclude_paths(temp_git_repo_with_remote):
    original_cwd = os.getcwd()
    os.chdir(temp_git_repo_with_remote)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31", exclude_paths=["docs/"])
        git_data = config.get_git_log_data()

        assert "Initial commit" in git_data
        assert "Second commit" in git_data
        assert "Third commit by Dev User" in git_data
        assert "Add feature.js" in git_data
        assert "file1.txt" in git_data
        assert "file2.txt" in git_data
        assert "src/feature.js" in git_data

        # Ensure excluded commit/file is NOT present
        assert "Update docs" not in git_data
        assert "docs/README.md" not in git_data
    finally:
        os.chdir(original_cwd)
