from datetime import datetime, timezone
import logging
import pytest

from dulwich.objects import Commit
from dulwich.repo import Repo
from git2df.dulwich.commit_walker import DulwichCommitWalker
from git2df.dulwich.commit_filters import DulwichCommitFilters
from git2df.dulwich.commit_formatter import DulwichCommitFormatter

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_dulwich_commit_walker(mocker):
    mock_filters = mocker.MagicMock(spec=DulwichCommitFilters)
    mock_formatter = mocker.MagicMock(spec=DulwichCommitFormatter)
    return DulwichCommitWalker(mock_filters, mock_formatter, "main")


@pytest.fixture
def mock_repo_with_commits(mocker):
    repo = mocker.MagicMock(spec=Repo)
    repo.path = "/mock/repo/path"

    # Create mock commits
    commit1 = mocker.MagicMock(spec=Commit)
    commit1.id.hex.return_value = "commit1hash"
    commit1.commit_time = datetime(
        2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc
    ).timestamp()

    commit2 = mocker.MagicMock(spec=Commit)
    commit2.id.hex.return_value = "commit2hash"
    commit2.commit_time = datetime(
        2023, 1, 2, 10, 0, 0, tzinfo=timezone.utc
    ).timestamp()

    commit3 = mocker.MagicMock(spec=Commit)
    commit3.id.hex.return_value = "commit3hash"
    commit3.commit_time = datetime(
        2023, 1, 3, 10, 0, 0, tzinfo=timezone.utc
    ).timestamp()

    # Mock the walker to yield commits
    repo.get_walker.return_value = [
        mocker.MagicMock(commit=commit1),
        mocker.MagicMock(commit=commit2),
        mocker.MagicMock(commit=commit3),
    ]
    repo.refs = mocker.MagicMock()
    repo.refs.__getitem__.return_value = "main_sha"
    return repo


def test_collect_and_filter_commits_no_filters(
    mock_dulwich_commit_walker, mock_repo_with_commits
):
    mock_dulwich_commit_walker.commit_filters.filter_commits_by_date.return_value = True

    result = mock_dulwich_commit_walker._collect_and_filter_commits(
        mock_repo_with_commits, None, None
    )
    assert len(result) == 3
    assert result[0].id.hex.return_value == "commit1hash"
    assert result[1].id.hex.return_value == "commit2hash"
    assert result[2].id.hex.return_value == "commit3hash"


def test_collect_and_filter_commits_with_since_filter(
    mock_dulwich_commit_walker, mock_repo_with_commits
):
    since_dt = datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

    def filter_side_effect(commit_datetime, since, until):
        return commit_datetime >= since

    mock_dulwich_commit_walker.commit_filters.filter_commits_by_date.side_effect = (
        filter_side_effect
    )

    result = mock_dulwich_commit_walker._collect_and_filter_commits(
        mock_repo_with_commits, since_dt, None
    )
    assert len(result) == 2
    assert result[0].id.hex.return_value == "commit2hash"
    assert result[1].id.hex.return_value == "commit3hash"


def test_collect_and_filter_commits_with_until_filter(
    mock_dulwich_commit_walker, mock_repo_with_commits
):
    until_dt = datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

    def filter_side_effect(commit_datetime, since, until):
        return commit_datetime < until

    mock_dulwich_commit_walker.commit_filters.filter_commits_by_date.side_effect = (
        filter_side_effect
    )

    result = mock_dulwich_commit_walker._collect_and_filter_commits(
        mock_repo_with_commits, None, until_dt
    )
    assert len(result) == 1
    assert result[0].id.hex.return_value == "commit1hash"


def test_collect_and_filter_commits_with_both_filters(
    mock_dulwich_commit_walker, mock_repo_with_commits
):
    since_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    until_dt = datetime(2023, 1, 3, 0, 0, 0, tzinfo=timezone.utc)

    def filter_side_effect(commit_datetime, since, until):
        return since <= commit_datetime < until

    mock_dulwich_commit_walker.commit_filters.filter_commits_by_date.side_effect = (
        filter_side_effect
    )

    result = mock_dulwich_commit_walker._collect_and_filter_commits(
        mock_repo_with_commits, since_dt, until_dt
    )
    assert len(result) == 1
    assert result[0].id.hex.return_value == "commit2hash"
