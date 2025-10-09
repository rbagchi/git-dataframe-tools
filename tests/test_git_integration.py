import pytest
import subprocess
import os
import sys
from pathlib import Path


from git_dataframe_tools.config_models import GitAnalysisConfig
from git2df import get_commits_df


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


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_get_git_log_data_integration_default(git_repo):
    original_cwd = os.getcwd()
    os.chdir(git_repo)
    try:
        config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-12-31")
        git_data_df = get_commits_df(
            repo_path=git_repo,
            since=config.start_date.isoformat(),
            until=config.end_date.isoformat(),
            author=config.author_query,
            merged_only=config.merged_only,
            include_paths=config.include_paths,
            exclude_paths=config.exclude_paths,
        )

        # Check for presence of expected authors and total number of commits
        assert not git_data_df.empty
        assert len(git_data_df) == 4  # 4 total commits in the fixture
        assert "commit_hash" in git_data_df.columns
        assert "parent_hash" in git_data_df.columns
        assert "author_name" in git_data_df.columns
        assert "author_email" in git_data_df.columns
        assert "commit_date" in git_data_df.columns
        assert "file_paths" in git_data_df.columns
        assert "change_type" in git_data_df.columns
        assert "additions" in git_data_df.columns
        assert "deletions" in git_data_df.columns
        assert "commit_message" in git_data_df.columns
        assert git_data_df["author_name"].nunique() == 3  # Default User, Test User and Dev User
        assert git_data_df["commit_hash"].nunique() == 4  # 4 unique commits

    finally:
        os.chdir(original_cwd)


def test_get_git_log_data_integration_merged_only(temp_git_repo_with_remote):
    config = GitAnalysisConfig(
        start_date="2025-01-01", end_date="2025-12-31", merged_only=True
    )
    git_data_df = get_commits_df(
        repo_path=temp_git_repo_with_remote,
        since=config.start_date.isoformat(),
        until=config.end_date.isoformat(),
        author=config.author_query,
        merged_only=config.merged_only,
        include_paths=config.include_paths,
        exclude_paths=config.exclude_paths,
    )

    # Expect no commits as the fixture does not create merge commits
    assert git_data_df.empty


def test_get_git_log_data_integration_include_paths(temp_git_repo_with_remote):
    config = GitAnalysisConfig(
        start_date="2025-01-01", end_date="2025-12-31", include_paths=["src/"]
    )
    git_data_df = get_commits_df(
        repo_path=temp_git_repo_with_remote,
        since=config.start_date.isoformat(),
        until=config.end_date.isoformat(),
        author=config.author_query,
        merged_only=config.merged_only,
        include_paths=config.include_paths,
        exclude_paths=config.exclude_paths,
    )

    assert not git_data_df.empty
    assert len(git_data_df) == 1  # 1 file change in src/
    assert (git_data_df["file_paths"] == "src/feature.js").all()
    assert (git_data_df["author_name"] == "Dev User").all()
    assert git_data_df["additions"].sum() == 1
    assert git_data_df["deletions"].sum() == 0


def test_get_git_log_data_integration_exclude_paths(temp_git_repo_with_remote):
    config = GitAnalysisConfig(
        start_date="2025-01-01", end_date="2025-12-31", exclude_paths=["docs/"]
    )
    git_data_df = get_commits_df(
        repo_path=temp_git_repo_with_remote,
        since=config.start_date.isoformat(),
        until=config.end_date.isoformat(),
        author=config.author_query,
        merged_only=config.merged_only,
        include_paths=config.include_paths,
        exclude_paths=config.exclude_paths,
    )

    assert not git_data_df.empty
    assert len(git_data_df) == 4  # 4 file changes after excluding docs/
    assert "docs/README.md" not in git_data_df["file_paths"].values
    assert (
        git_data_df["author_name"].nunique() == 2
    )  # Both Test User and Dev User still have commits
    assert (
        git_data_df[git_data_df["author_name"] == "Test User"].shape[0] == 2
    )  # 2 file changes by Test User after exclusion
    assert (
        git_data_df[git_data_df["author_name"] == "Dev User"].shape[0] == 2
    )  # 2 file changes by Dev User after exclusion
    assert git_data_df["additions"].sum() == 4  # 1+1+1+1


def test_scoreboard_with_df_path(temp_git_repo_with_remote, tmp_path):
    """Integration test: scoreboard operates on a parquet file dumped by git-df."""
    # 1. Run git-df to create a parquet file
    df_output_file = tmp_path / "commits.parquet"
    project_root = Path(__file__).parent.parent # Adjust path to get to the project root
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")

    git_df_command = [
        "git-df",
        "--repo-path",
        str(temp_git_repo_with_remote),
        "--output",
        str(df_output_file),
        "--since",
        "2025-01-01",
        "--until",
        "2025-12-31",
    ]
    git_df_result = subprocess.run(
        git_df_command, capture_output=True, text=True, check=True, env=env
    )
    assert git_df_result.returncode == 0
    assert df_output_file.exists()

    # 2. Run git-scoreboard with the generated parquet file
    scoreboard_command = [
        "git-scoreboard",
        "--df-path",
        str(df_output_file),
        "--since",
        "2025-01-01",
        "--until",
        "2025-12-31",
    ]
    scoreboard_result = subprocess.run(
        scoreboard_command, capture_output=True, text=True, check=True, env=env
    )
    assert scoreboard_result.returncode == 0

    # 3. Assert on scoreboard output
    output = scoreboard_result.stdout
    assert "Git Author Ranking by Diff Size" in output
    assert "Test User" in output
    assert "Dev User" in output
    assert "Total Diff" in output
    assert "Commits" in output
