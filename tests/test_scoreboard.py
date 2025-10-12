import pytest
import os
import subprocess
from typing import List
import re

from tests.conftest import sample_commits

# --- Unit tests for argument parsing ---


def test_main_author_and_me_mutually_exclusive():
    result = subprocess.run(
        ["git-scoreboard", "--repo-path", ".", "--author", "test", "--me"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Error: Cannot use both --author and --me options together" in result.stderr


# --- Integration tests for CLI ---


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_basic(git_repo):
    """Test the git-scoreboard CLI with basic arguments."""
    os.chdir(git_repo)

    result = subprocess.run(
        ["git-scoreboard", "--repo-path", "."], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Git Author Ranking by Diff Size" in result.stdout
    assert "Test User" in result.stdout
    assert "Dev User" in result.stdout


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_author_filter(git_repo):
    """Test the git-scoreboard CLI with an author filter."""
    os.chdir(git_repo)

    result = subprocess.run(
        ["git-scoreboard", "--repo-path", ".", "--author", "Test User"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Author Stats for 'Test User'" in result.stdout
    assert "Test User" in result.stdout
    assert "Dev User" not in result.stdout


def _assert_markdown_header(stdout: str) -> None:
    header_pattern = r"\|\s*Rank\s*\|\s*Author\s*\|\s*Lines Added\s*\|\s*Lines Deleted\s*\|\s*Total Diff\s*\|\s*Commits\s*\|\s*Diff D\s*\|\s*Comm D\s*\|"
    assert re.search(header_pattern, stdout)

def _assert_markdown_separator(stdout: str) -> None:
    separator_pattern = r"\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|\s*:?-+\s*:?\s*\|"
    assert re.search(separator_pattern, stdout)

def _assert_markdown_authors(stdout: str, authors: List[str]) -> None:
    for author in authors:
        assert author in stdout

@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_scoreboard_cli_markdown_output(git_repo):
    """Test the git-scoreboard CLI with markdown output format."""
    os.chdir(git_repo)

    result = subprocess.run(
        ["git-scoreboard", "--repo-path", ".", "--format", "markdown"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    import re

    _assert_markdown_header(result.stdout)
    _assert_markdown_separator(result.stdout)
    _assert_markdown_authors(result.stdout, ["Test User", "Dev User", "Default User"])
