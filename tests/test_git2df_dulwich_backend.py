from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone, timedelta  # Import timedelta
import pytest
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from git2df.dulwich_backend import DulwichRemoteBackend
from dulwich.objects import Commit, Tree, Blob
from dulwich.diff_tree import TreeChange, TreeEntry  # Corrected import


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



@patch("git2df.dulwich_backend.HttpGitClient")
@patch("git2df.dulwich_backend.Repo")
@patch("git2df.dulwich_backend.datetime")  # Patch datetime module
def test_get_raw_log_output_basic_fetch(
    mock_datetime_module, mock_repo_class, mock_http_git_client_class
):
    # Arrange
    remote_url = "https://github.com/test/repo"
    remote_branch = "main"

    # Mock datetime.datetime.now() to a fixed point in time
    fixed_now = datetime(2024, 10, 11, 12, 0, 0, tzinfo=timezone.utc)
    mock_datetime_module.datetime = MagicMock(
        spec=datetime
    )  # Mock datetime.datetime class
    mock_datetime_module.datetime.now.return_value = fixed_now
    mock_datetime_module.datetime.fromtimestamp = (
        datetime.fromtimestamp
    )  # Ensure original fromtimestamp is used
    mock_datetime_module.timedelta = timedelta  # Ensure original timedelta is used
    mock_datetime_module.timezone = timezone  # Ensure original timezone is used

    # Mock HttpGitClient and its fetch method
    mock_http_git_client = MagicMock()
    mock_http_git_client_class.return_value = mock_http_git_client

    mock_fetch_result = MagicMock()
    mock_fetch_result.refs = {b"refs/heads/main": b"commit_sha_head"}
    mock_http_git_client.fetch.return_value = mock_fetch_result

    # Mock Repo and its methods
    mock_repo = MagicMock()
    mock_repo_class.init.return_value = mock_repo

    # Mock commit and its parent
    commit_time = datetime(2024, 10, 10, 10, 0, 0, tzinfo=timezone.utc)
    mock_commit_head = create_mock_commit(
        "commit_sha_head",
        ["commit_sha_parent"],
        "Author One",
        "author1@example.com",
        commit_time,
        "Subject 1\n\nBody 1",
        "tree_sha_head",
    )
    mock_commit_parent = create_mock_commit(
        "commit_sha_parent",
        [],
        "Author Zero",
        "author0@example.com",
        datetime(2024, 10, 9, 9, 0, 0, tzinfo=timezone.utc),
        "Subject 0",
        "tree_sha_parent",
    )

    # Mock tree objects
    mock_tree_head = create_mock_tree("tree_sha_head")
    mock_tree_parent = create_mock_tree("tree_sha_parent")

    # Mock blob objects for file changes
    mock_blob_old = create_mock_blob("blob_sha_old", "line1\nline2")
    mock_blob_new = create_mock_blob("blob_sha_new", "line1\nline2\nline3")

    # Mock tree_changes
    mock_tree_changes_return_value = [
        MagicMock(
            type=b"modify",
            old=MagicMock(path=b"file1.txt", sha=b"blob_sha_old"),
            new=MagicMock(path=b"file1.txt", sha=b"blob_sha_new"),
        )
    ]
    with patch("dulwich.diff_tree.tree_changes", return_value=mock_tree_changes_return_value):
        mock_repo.get_object.side_effect = lambda sha: {
            b"commit_sha_parent": mock_commit_parent,
            b"blob_sha_old": mock_blob_old,
            b"blob_sha_new": mock_blob_new,
        }.get(sha)
        mock_repo.get_walker.return_value = [MagicMock(commit=mock_commit_head)]

        backend = DulwichRemoteBackend(remote_url, remote_branch)

        # Act
        output = backend.get_raw_log_output(since="2 days ago")  # Changed since
    # Assert
    expected_output = (
        f"|||commit_sha_head|||{'commit_sha_parent'.encode('ascii').hex()}|||Author One|||author1@example.com|||{commit_time.isoformat()}|||Subject 1\n"
        "1\t0\tfile1.txt"
    )
    assert output == expected_output
    mock_http_git_client_class.assert_called_once_with(remote_url)
    mock_http_git_client.fetch.assert_called_once()
    mock_repo_class.init.assert_called_once()
    mock_repo.get_walker.assert_called_once()
    mock_repo.get_object.assert_called()


@patch("git2df.dulwich_backend.HttpGitClient")
@patch("git2df.dulwich_backend.Repo")
@patch("git2df.dulwich_backend.datetime")  # Patch datetime module
@patch("dulwich.diff_tree.tree_changes")
def test_get_raw_log_output_initial_commit(
    mock_get_tree_changes,
    mock_datetime_module,
    mock_repo_class,
    mock_http_git_client_class,
):
    # Arrange
    remote_url = "https://github.com/test/repo"
    remote_branch = "main"

    # Mock datetime.datetime.now() to a fixed point in time
    fixed_now = datetime(
        2024, 10, 11, 12, 0, 0, tzinfo=timezone.utc
    )  # Changed fixed_now
    mock_datetime_module.datetime = MagicMock(
        spec=datetime
    )  # Mock datetime.datetime class
    mock_datetime_module.datetime.now.return_value = fixed_now
    mock_datetime_module.datetime.fromtimestamp = (
        datetime.fromtimestamp
    )  # Ensure original fromtimestamp is used
    mock_datetime_module.timedelta = timedelta  # Ensure original timedelta is used
    mock_datetime_module.timezone = timezone  # Ensure original timezone is used

    mock_http_git_client = MagicMock()
    mock_http_git_client_class.return_value = mock_http_git_client

    mock_fetch_result = MagicMock()
    mock_fetch_result.refs = {b"refs/heads/main": b"initial_commit_sha"}
    mock_http_git_client.fetch.return_value = mock_fetch_result

    mock_repo = MagicMock()
    mock_repo_class.init.return_value = mock_repo

    commit_time = datetime(2024, 10, 10, 10, 0, 0, tzinfo=timezone.utc)
    mock_initial_commit = create_mock_commit(
        "initial_commit_sha",
        [],  # No parents for initial commit
        "Author Initial",
        "initial@example.com",
        commit_time,
        "Initial commit",
        "initial_tree_sha",
    )

    mock_tree = create_mock_tree("initial_tree_sha")
    mock_blob = create_mock_blob("blob_sha_file1", "content of file1")

    mock_get_tree_changes.return_value = [
        MagicMock(
            type=b"add",
            old=MagicMock(path=None, sha=None),
            new=MagicMock(path=b"file1.txt", sha=b"blob_sha_file1"),
        )
    ]
    # Mock get_object for the initial commit and its tree/blobs
    mock_repo.get_object.side_effect = lambda sha: {
        b"blob_sha_file1": mock_blob,
        b"initial_commit_sha": mock_initial_commit,
        b"initial_tree_sha": mock_tree,
    }.get(sha)
    # Mock get_walker for initial commit's tree walk
    mock_tree_entry = MagicMock()
    mock_tree_entry.path = b"file1.txt"
    mock_tree_entry.sha = b"blob_sha_file1"
    mock_repo.get_walker.return_value = [MagicMock(commit=mock_initial_commit)]  # First call for commits

    backend = DulwichRemoteBackend(remote_url, remote_branch)

    # Act
    output = backend.get_raw_log_output(since="2 days ago")  # Changed since

    # Assert
    expected_output = (
        f"|||initial_commit_sha||||||Author Initial|||initial@example.com|||{commit_time.isoformat()}|||Initial commit\n"
        "1\t0\tfile1.txt"
    )
    assert output == expected_output
    assert output == expected_output

    mock_http_git_client_class.assert_called_once_with(remote_url)
    mock_http_git_client.fetch.assert_called_once()
    mock_repo_class.init.assert_called_once()
    # get_walker is called once for commits
    mock_repo.get_walker.assert_called_once()
    mock_repo.get_object.assert_called()
