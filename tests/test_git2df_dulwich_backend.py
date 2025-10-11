from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import List
import logging

from git2df.dulwich.backend import DulwichRemoteBackend
from dulwich.objects import Commit, Tree, Blob
from dulwich.repo import Repo
from .conftest import _create_dulwich_commit

logger = logging.getLogger(__name__)


# Helper to create a mock commit object
def create_mock_commit(
    sha: str,
    parents: List[str],
    author_name: str,
    author_email: str,
    timestamp: datetime,
    message: str,
    tree_sha: str,
) -> MagicMock:
    mock_commit = MagicMock(spec=Commit)
    mock_commit.id = MagicMock(spec=bytes)  # Mock the id attribute
    mock_commit.id.hex.return_value = sha  # Mock the hex() method of the id
    # Mock parent objects: each parent should be a MagicMock with an 'id' attribute (bytes) and a 'hex' method
    mock_parents = []
    for p_sha in parents:
        mock_parents.append(p_sha.encode("ascii"))
    mock_commit.parents = mock_parents
    mock_commit.author = f"{author_name} <{author_email}>".encode("utf-8")
    mock_commit.commit_time = int(timestamp.timestamp())
    mock_commit.message = message.encode("utf-8")
    mock_commit.tree = tree_sha.encode("ascii")
    return mock_commit


# Helper to create a mock tree object
def create_mock_tree(sha: str) -> MagicMock:
    mock_tree = MagicMock(spec=Tree)
    mock_tree.id = sha.encode("ascii")
    return mock_tree


# Helper to create a mock blob object
def create_mock_blob(sha: str, content: str) -> MagicMock:
    mock_blob = MagicMock(spec=Blob)
    mock_blob.id = sha.encode("ascii")
    mock_blob.as_pretty_string.return_value = "\n".join(content.splitlines())
    return mock_blob


# Helper to create a mock TreeChange object (formerly create_mock_change)


@patch("git2df.dulwich.commit_formatter.datetime")  # Patch datetime module in commit_formatter
@patch("git2df.dulwich.commit_filters.datetime")  # Patch datetime module in commit_filters
@patch("git2df.dulwich.date_utils.datetime")  # Patch datetime module in date_utils
@patch("time.time")  # Patch time.time
def test_get_raw_log_output_basic_fetch(mock_time, mock_date_utils_datetime_module, mock_commit_filters_datetime_module, mock_commit_formatter_datetime_module, dulwich_repo, caplog):
    caplog.set_level(logging.DEBUG)
    # Arrange
    remote_branch = "main"

    # Mock datetime.datetime.now() to a fixed point in time
    fixed_now = datetime(2024, 10, 11, 12, 0, 0, tzinfo=timezone.utc)

    # Apply mocks to commit_formatter's datetime
    mock_commit_formatter_datetime_module.datetime = MagicMock(spec=datetime)
    mock_commit_formatter_datetime_module.datetime.now.return_value = fixed_now
    mock_commit_formatter_datetime_module.datetime.fromtimestamp = datetime.fromtimestamp
    mock_commit_formatter_datetime_module.timedelta = timedelta
    mock_commit_formatter_datetime_module.timezone = timezone

    # Apply mocks to date_utils' datetime
    mock_date_utils_datetime_module.datetime = MagicMock(spec=datetime)
    mock_date_utils_datetime_module.datetime.now.return_value = fixed_now
    mock_date_utils_datetime_module.datetime.fromtimestamp = datetime.fromtimestamp
    mock_date_utils_datetime_module.timedelta = timedelta
    mock_date_utils_datetime_module.timezone = timezone

    # Apply mocks to commit_filters' datetime
    mock_commit_filters_datetime_module.datetime = MagicMock(spec=datetime)
    mock_commit_filters_datetime_module.datetime.now.return_value = fixed_now
    mock_commit_filters_datetime_module.datetime.fromtimestamp = datetime.fromtimestamp
    mock_commit_filters_datetime_module.timedelta = timedelta
    mock_commit_filters_datetime_module.timezone = timezone

    mock_time.return_value = (
        fixed_now.timestamp()
    )  # Make time.time return the fixed timestamp

    repo = Repo(dulwich_repo)

    commit_time_parent = datetime(2024, 10, 9, 9, 0, 0, tzinfo=timezone.utc)
    commit_time_head = datetime(2024, 10, 10, 10, 0, 0, tzinfo=timezone.utc)

    # Create parent commit
    parent_commit_id = _create_dulwich_commit(
        repo,
        {"file1.txt": "initial content"},
        "Subject 0",
        "Author Zero",
        "author0@example.com",
                int(commit_time_parent.timestamp()),
            )
    
    # Create head commit
    head_commit_id = _create_dulwich_commit(
                repo,
                {"file1.txt": "modified content"},
                "Subject 1\n\nBody 1",
                "Author One",
                "author1@example.com",
                int(commit_time_head.timestamp()),
            )
    
    backend = DulwichRemoteBackend(repo.path, remote_branch)
    # Act
    output = backend.get_raw_log_output(since="3 days ago")  # Changed since
    # Assert
    head_commit = repo[head_commit_id]
    parent_commit = repo[parent_commit_id]

    expected_output = (
        f"@@@COMMIT@@@{head_commit.id.hex()}@@@FIELD@@@"
        f"{parent_commit.id.hex()}@@@FIELD@@@"
        f"Author One@@@FIELD@@@"
        f"author1@example.com@@@FIELD@@@"
        f"{commit_time_head.isoformat()}\t{int(commit_time_head.timestamp())}@@@FIELD@@@"
        f"---MSG_START---Subject 1\n\nBody 1---MSG_END---\n"
        f"1\t1\tM\tfile1.txt\n"
        f"@@@COMMIT@@@{parent_commit.id.hex()}@@@FIELD@@@"
        f"@@@FIELD@@@"
        f"Author Zero@@@FIELD@@@"
        f"author0@example.com@@@FIELD@@@"
        f"{commit_time_parent.isoformat()}\t{int(commit_time_parent.timestamp())}@@@FIELD@@@"
        f"---MSG_START---Subject 0---MSG_END---\n"
        f"1\t0\tA\tfile1.txt"
    )
    assert output == expected_output