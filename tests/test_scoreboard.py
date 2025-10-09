import pytest
import subprocess
import os
from unittest.mock import patch
import sys

from git_dataframe_tools.cli import scoreboard
from tests.conftest import sample_commits

# --- Unit tests for argument parsing ---


@patch.object(sys, "argv", ["scoreboard.py", "."])
def test_parse_arguments_default():
    args = scoreboard.parse_arguments()
    assert args.repo_path == "."
    assert args.since is None
    assert args.until is None
    assert args.author is None
    assert args.me is False
    assert args.merges is False
    assert args.path is None
    assert args.exclude_path is None
    assert args.default_period == "3 months ago"
    assert args.df_path is None
    assert args.force_version_mismatch is False
    assert args.verbose is False
    assert args.debug is False


@patch.object(
    sys,
    "argv",
    [
        "scoreboard.py",
        "--since",
        "2024-01-01",
        "-U",
        "2024-03-31",
        "-a",
        "John Doe",
        "--me",
        "--merges",
        "-p",
        "src",
        "-p",
        "docs",
        "-x",
        "tests",
        "--default-period",
        "6 months",
        "--df-path",
        "data.parquet",
        "--force-version-mismatch",
        "-v",
        "-d",
    ],
)
def test_parse_arguments_all_options():
    args = scoreboard.parse_arguments()
    assert args.repo_path == "."
    assert args.since == "2024-01-01"
    assert args.until == "2024-03-31"
    assert args.author == "John Doe"
    assert args.me is True
    assert args.merges is True
    assert args.path == ["src", "docs"]
    assert args.exclude_path == ["tests"]
    assert args.default_period == "6 months"
    assert args.df_path == "data.parquet"
    assert args.force_version_mismatch is True
    assert args.verbose is True
    assert args.debug is True


@patch.object(sys, "argv", ["scoreboard.py", ".", "--author", "test", "--me"])
@patch("git_dataframe_tools.cli._validation.logger")
def test_main_author_and_me_mutually_exclusive(mock_logger):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "Error: Cannot use both --author and --me options together"
    )


# --- Integration tests for CLI ---


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_basic(git_repo):
    """Test the git-scoreboard CLI with basic arguments."""
    os.chdir(git_repo)

    command = [
        "git-scoreboard",
        ".",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert "Git Author Ranking by Diff Size" in result.stdout
    assert "Test User" in result.stdout
    assert "Dev User" in result.stdout


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_author_filter(git_repo):
    """Test the git-scoreboard CLI with an author filter."""
    os.chdir(git_repo)

    command = [
        "git-scoreboard",
        ".",
        "--author",
        "Test User",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    assert "Author Stats for 'Test User'" in result.stdout
    assert "Test User" in result.stdout
    assert "Dev User" not in result.stdout
    assert "Default User" not in result.stdout
