import pytest
import os

from git_dataframe_tools.cli import scoreboard
from tests.conftest import sample_commits
from typer.testing import CliRunner

runner = CliRunner()

# --- Unit tests for argument parsing ---


def test_main_author_and_me_mutually_exclusive():
    result = runner.invoke(scoreboard.app, ["--repo-path", ".", "--author", "test", "--me"])
    assert result.exit_code == 1
    assert "Error: Cannot use both --author and --me options together" in result.stderr


# --- Integration tests for CLI ---


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_basic(git_repo):
    """Test the git-scoreboard CLI with basic arguments."""
    os.chdir(git_repo)

    result = runner.invoke(scoreboard.app, ["--repo-path", "."])
    assert result.exit_code == 0
    assert "Git Author Ranking by Diff Size" in result.stdout
    assert "Test User" in result.stdout
    assert "Dev User" in result.stdout


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_author_filter(git_repo):
    """Test the git-scoreboard CLI with an author filter."""
    os.chdir(git_repo)

    result = runner.invoke(scoreboard.app, ["--repo-path", ".", "--author", "Test User"])
    assert result.exit_code == 0
    assert "Author Stats for 'Test User'" in result.stdout
    assert "Test User" in result.stdout
    assert "Dev User" not in result.stdout
    assert "Default User" not in result.stdout
