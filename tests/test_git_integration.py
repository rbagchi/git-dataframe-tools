import pytest
import subprocess
import os

from git_dataframe_tools.config_models import GitAnalysisConfig
from git_dataframe_tools.git_python_repo_info_provider import GitPythonRepoInfoProvider


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

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )

    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    print("DEBUG: Test User configured.")

    # Add remote

    subprocess.run(
        ["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True
    )

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

    subprocess.run(
        ["git", "config", "user.email", "dev@example.com"], cwd=repo_path, check=True
    )

    subprocess.run(
        ["git", "config", "user.name", "Dev User"], cwd=repo_path, check=True
    )

    print("DEBUG: Dev User configured.")

    (repo_path / "file1.txt").write_text("hello world again")

    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)

    subprocess.run(
        ["git", "commit", "-m", "Third commit by Dev User"], cwd=repo_path, check=True
    )

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


# Test GitAnalysisConfig._get_current_git_user


def test_get_current_git_user_integration(temp_git_repo_with_remote):

    original_cwd = os.getcwd()

    os.chdir(temp_git_repo_with_remote)

    try:

        repo_info_provider = GitPythonRepoInfoProvider()

        config = GitAnalysisConfig(
            use_current_user=True, repo_info_provider=repo_info_provider
        )

        # The last user configured in the fixture is 'Dev User'

        assert config.current_user_name == "Dev User"

        assert config.current_user_email == "dev@example.com"

    finally:

        os.chdir(original_cwd)
