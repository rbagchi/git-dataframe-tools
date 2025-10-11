import pytest
import os

from git_dataframe_tools.cli import scoreboard
from tests.conftest import sample_commits
from typer.testing import CliRunner

runner = CliRunner()

# --- Unit tests for argument parsing ---


def test_main_author_and_me_mutually_exclusive():
    result = runner.invoke(
        scoreboard.app, ["--repo-path", ".", "--author", "test", "--me"]
    )
    assert result.exit_code == 1
    assert "Error: Cannot use both --author and --me options together" in result.stdout


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

    result = runner.invoke(
        scoreboard.app, ["--repo-path", ".", "--author", "Test User"]
    )
    assert result.exit_code == 0
    assert "Author Stats for 'Test User'" in result.stdout
    assert "Test User" in result.stdout
    assert "Dev User" not in result.stdout


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_markdown_output(git_repo):
    """Test the git-scoreboard CLI with markdown output format."""
    os.chdir(git_repo)

    result = runner.invoke(scoreboard.app, ["--repo-path", ".", "--format", "markdown"])
    assert result.exit_code == 0
    import re
    # Check for the header row with flexible whitespace
    header_pattern = r"\|\s*Rank\s*\|\s*Author\s*\|\s*Lines Added\s*\|\s*Lines Deleted\s*\|\s*Total Diff\s*\|\s*Commits\s*\|\s*Diff D\s*\|\s*Comm D\s*\|"
    assert re.search(header_pattern, result.stdout)

    # Check for the separator line with flexible whitespace and alignment characters
    separator_pattern = r"\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|"
    assert re.search(separator_pattern, result.stdout)

    # Check for author names within the Markdown table content
    assert "Test User" in result.stdout
    assert "Dev User" in result.stdout
    assert "ranjan" in result.stdout # Assuming 'ranjan' is the default user in sample_commits
