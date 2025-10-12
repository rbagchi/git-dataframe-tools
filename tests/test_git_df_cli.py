import pytest
import subprocess
import pyarrow.parquet as pq
import os
from tests.conftest import sample_commits


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_git_df_cli_basic(git_repo, tmp_path):
    """Test the git-df CLI with basic arguments."""
    output_file = tmp_path / "commits.parquet"

    os.chdir(git_repo)

    command = [
        "git-df",
        "--output",
        str(output_file),
        "--repo-path",
        ".",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    table = pq.read_table(output_file)
    df = table.to_pandas()
    assert not df.empty
    # 1 initial commit + 3 sample commits
    assert len(df) == 4
    assert "commit_hash" in df.columns
    assert "author_name" in df.columns


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_git_df_cli_author_filter(git_repo, tmp_path):
    """Test the git-df CLI with an author filter."""
    output_file = tmp_path / "author_commits.parquet"
    os.chdir(git_repo)

    command = [
        "git-df",
        "--output",
        str(output_file),
        "--repo-path",
        ".",
        "--author",
        "Test User",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert output_file.exists()

    df = pq.read_table(output_file).to_pandas()
    assert not df.empty
    assert (df["author_name"] == "Test User").all()


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_git_df_cli_no_commits_found(git_repo, tmp_path):
    """Test the git-df CLI when no commits are found."""
    output_file = tmp_path / "no_commits.parquet"
    os.chdir(git_repo)

    command = [
        "git-df",
        "--output",
        str(output_file),
        "--repo-path",
        ".",
        "--since",
        "1999-01-01",
        "--until",
        "1999-12-31",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0
    assert output_file.exists()

    df = pq.read_table(output_file).to_pandas()
    assert df.empty
    assert "No commits found" in result.stderr
