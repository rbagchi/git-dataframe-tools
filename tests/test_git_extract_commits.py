import pytest
import subprocess
import os
import pandas as pd

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

def test_git_extract_commits_basic(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "commits.parquet"
    command = [
        "git-extract-commits",
        str(temp_git_repo_with_remote),
        "--output", str(output_file),
        "--since", "2025-01-01",
        "--until", "2025-12-31"
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    df = pd.read_parquet(output_file)
    assert not df.empty
    assert len(df) == 2 # 2 unique authors in the fixture
    assert df['num_commits'].sum() == 5 # 5 total commits in the fixture
    assert "commit_hashes" in df.columns
    assert "author_name" in df.columns
    assert "author_email" in df.columns
    assert "added" in df.columns
    assert "deleted" in df.columns

def test_git_extract_commits_with_author_filter(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "author_commits.parquet"
    command = [
        "git-extract-commits",
        str(temp_git_repo_with_remote),
        "--output", str(output_file),
        "--author", "Test User"
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    df = pd.read_parquet(output_file)
    assert not df.empty
    assert len(df) == 1 # Only one author (Test User)
    assert df['author_name'].iloc[0] == "Test User"
    assert df['num_commits'].iloc[0] == 2 # 2 commits by Test User

def test_git_extract_commits_with_path_filter(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "path_commits.parquet"
    command = [
        "git-extract-commits",
        str(temp_git_repo_with_remote),
        "--output", str(output_file),
        "--path", "src/"
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    df = pd.read_parquet(output_file)
    assert not df.empty
    # Only 'Add feature.js' commit is in src/ and it's by Dev User
    assert len(df) == 1
    assert df['author_name'].iloc[0] == "Dev User"
    assert df['num_commits'].iloc[0] == 1

def test_git_extract_commits_with_exclude_path_filter(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "exclude_path_commits.parquet"
    command = [
        "git-extract-commits",
        str(temp_git_repo_with_remote),
        "--output", str(output_file),
        "--exclude-path", "docs/"
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    df = pd.read_parquet(output_file)
    assert not df.empty
    assert len(df) == 2 # 2 unique authors
    assert df['num_commits'].sum() == 4 # 5 total commits, 1 in docs excluded.

def test_git_extract_commits_no_commits_found(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "no_commits.parquet"
    command = [
        "git-extract-commits",
        str(temp_git_repo_with_remote),
        "--output", str(output_file),
        "--since", "1999-01-01",
        "--until", "1999-12-31"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0 # Should exit cleanly even if no commits
    assert not output_file.exists() # No file should be created if no commits
    assert "No commits found" in result.stdout # Check for warning message
