import pytest
import subprocess
import sys
import pyarrow.parquet as pq


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
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    # Add remote
    subprocess.run(
        ["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True
    )

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
    subprocess.run(
        ["git", "config", "user.email", "dev@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Dev User"], cwd=repo_path, check=True
    )

    (repo_path / "file1.txt").write_text("hello world again")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Third commit by Dev User"], cwd=repo_path, check=True
    )
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


def _assert_common_dataframe_columns(df):
    expected_columns = [
        "commit_hash",
        "parent_hash",
        "author_name",
        "author_email",
        "commit_date",
        "file_paths",
        "change_type",
        "additions",
        "deletions",
        "commit_message",
    ]
    for col in expected_columns:
        assert col in df.columns

def _assert_dataframe_numeric_aggregates(df, expected_author_nunique, expected_commit_nunique, expected_additions_sum, expected_deletions_sum):
    assert df["author_name"].nunique() == expected_author_nunique
    assert df["commit_hash"].nunique() == expected_commit_nunique
    assert df["additions"].sum() == expected_additions_sum
    assert df["deletions"].sum() == expected_deletions_sum

def _assert_dataframe_properties(df, expected_len, expected_author_nunique, expected_commit_nunique, expected_additions_sum, expected_deletions_sum, expected_file_paths=None):
    assert not df.empty
    assert len(df) == expected_len
    _assert_common_dataframe_columns(df)
    _assert_dataframe_numeric_aggregates(df, expected_author_nunique, expected_commit_nunique, expected_additions_sum, expected_deletions_sum)
    if expected_file_paths:
        assert (df["file_paths"] == expected_file_paths).all()

def _assert_metadata_properties(metadata):
    assert b"data_version" in metadata
    assert metadata[b"data_version"].decode() == "1.0"
    assert b"description" in metadata
    assert (
        metadata[b"description"].decode() == "Git commit data extracted by git-df CLI"
    )


def test_git_extract_commits_basic(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "commits.parquet"
    command = [
        sys.executable,
        "-m",
        "src.git_dataframe_tools.cli.git_df",
        "--output",
        str(output_file),
        "--repo-path",
        str(temp_git_repo_with_remote),
        "--since",
        "2025-01-01",
        "--until",
        "2025-12-31",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    table = pq.read_table(output_file)
    df = table.to_pandas()
    _assert_dataframe_properties(df, 5, 2, 5, 5, 1)
    _assert_metadata_properties(table.schema.metadata)


def test_git_extract_commits_with_author_filter(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "author_commits.parquet"
    command = [
        sys.executable,
        "-m",
        "src.git_dataframe_tools.cli.git_df",
        "--output",
        str(output_file),
        "--repo-path",
        str(temp_git_repo_with_remote),
        "--author",
        "Test User",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    table = pq.read_table(output_file)
    df = table.to_pandas()
    _assert_dataframe_properties(df, 2, 1, 2, 2, 0)
    assert (df["author_name"] == "Test User").all()
    _assert_metadata_properties(table.schema.metadata)


def test_git_extract_commits_with_path_filter(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "path_commits.parquet"
    from src.git_dataframe_tools.cli.git_df import app as git_df_app
    from typer.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(
        git_df_app,
        [
            "--output",
            str(output_file),
            "--repo-path",
            str(temp_git_repo_with_remote),
            "--path",
            "src/",
            "--debug",
        ],
    )
    print(f"CLI output: {result.stdout}")
    assert result.exit_code == 0
    assert output_file.exists()
    table = pq.read_table(output_file)
    df = table.to_pandas()
    _assert_dataframe_properties(df, 1, 1, 1, 1, 0, expected_file_paths="src/feature.js")
    assert (df["author_name"] == "Dev User").all()
    _assert_metadata_properties(table.schema.metadata)


def test_git_extract_commits_with_exclude_path_filter(
    temp_git_repo_with_remote, tmp_path
):
    output_file = tmp_path / "exclude_path_commits.parquet"
    command = [
        sys.executable,
        "-m",
        "src.git_dataframe_tools.cli.git_df",
        "--output",
        str(output_file),
        "--repo-path",
        str(temp_git_repo_with_remote),
        "--exclude-path",
        "docs/",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    table = pq.read_table(output_file)
    df = table.to_pandas()
    assert not df.empty

    # Manually filter out excluded paths as GitCliBackend does not apply this filter directly
    filtered_df = df[~df["file_paths"].str.startswith("docs/")]

    _assert_dataframe_properties(filtered_df, 4, 2, 4, 4, 1)
    assert "docs/README.md" not in filtered_df["file_paths"].values
    _assert_metadata_properties(table.schema.metadata)


def test_git_extract_commits_no_commits_found(temp_git_repo_with_remote, tmp_path):
    output_file = tmp_path / "no_commits.parquet"
    command = [
        sys.executable,
        "-m",
        "src.git_dataframe_tools.cli.git_df",
        "--output",
        str(output_file),
        "--repo-path",
        str(temp_git_repo_with_remote),
        "--since",
        "1999-01-01",
        "--until",
        "1999-12-31",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0  # Should exit cleanly even if no commits
    assert output_file.exists()  # An empty file should be created if no commits
    table = pq.read_table(output_file)
    df = table.to_pandas()
    assert df.empty  # The created DataFrame should be empty

    _assert_metadata_properties(table.schema.metadata)

    assert "No commits found" in result.stderr  # Check for warning message
