import pandas as pd
from unittest.mock import patch, MagicMock
from git2df import get_commits_df
from git2df.git_parser import GitLogEntry, FileChange
from datetime import datetime, timezone
import pytest # Added import

# Mock data for commit-centric output
MOCKED_RAW_LOG_OUTPUT = (
    "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
    "10\\t5\\tfile1.txt\n"
    "\n"
    "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T11:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---\n"
    "20\\t0\\tfile2.py\n"
)

MOCKED_PARSED_DATA_RAW_BLOCKS = [
    [
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---",
        "10\\t5\\tfile1.txt",
    ],
    [
        "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T11:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---",
        "20\\t0\\tfile2.py",
    ],
]

MOCKED_PARSED_DATA = [
    {
        "commit_hash": "commit1hash",
        "parent_hash": "parent1hash",
        "author_name": "Author One",
        "author_email": "author1@example.com",
        "commit_date": datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        "commit_message": "Subject 1",
        "file_paths": "file1.txt",
        "change_type": "M",
        "additions": 10,
        "deletions": 5,
    },
    {
        "commit_hash": "commit2hash",
        "parent_hash": None,
        "author_name": "Author Two",
        "author_email": "author2@example.com",
        "commit_date": datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
        "commit_message": "Subject 2",
        "file_paths": "file2.py",
        "change_type": "A",
        "additions": 20,
        "deletions": 0,
    },
]

MOCKED_GIT_LOG_ENTRIES = [
    GitLogEntry(
        commit_hash="commit1hash",
        parent_hashes=["parent1hash"],
        author_name="Author One",
        author_email="author1@example.com",
        commit_date=datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        commit_timestamp=1672531200,  # Dummy timestamp for 2023-01-01 10:00:00 UTC
        commit_message="Subject 1",
        file_changes=[
            FileChange("file1.txt", 10, 5, "M"),
        ],
    ),
    GitLogEntry(
        commit_hash="commit2hash",
        parent_hashes=[],
        author_name="Author Two",
        author_email="author2@example.com",
        commit_date=datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
        commit_timestamp=1672617600,  # Dummy timestamp for 2023-01-02 11:00:00 UTC
        commit_message="Subject 2",
        file_changes=[
            FileChange("file2.py", 20, 0, "A"),
        ],
    ),
]

MOCKED_DF = pd.DataFrame(MOCKED_PARSED_DATA)


@pytest.mark.parametrize("local_backend_type", ["cli", "pygit2"])
@patch("git2df.build_commits_df")
@patch("git2df._get_git_backend")
def test_get_commits_df_with_filters(
    mock_get_git_backend,
    mock_build_commits_df,
    local_backend_type,
):
    # Setup mocks
    mock_backend_instance = MagicMock()
    mock_get_git_backend.return_value = mock_backend_instance
    mock_backend_instance.get_log_entries.return_value = MOCKED_GIT_LOG_ENTRIES
    mock_build_commits_df.return_value = MOCKED_DF

    repo_path = "/test/another_repo"
    since_arg = "2.weeks"
    grep_arg = "feature"

    # Call the function under test
    df = get_commits_df(repo_path, since=since_arg, grep=grep_arg, local_backend_type=local_backend_type)

    # Assertions
    mock_get_git_backend.assert_called_once_with(repo_path, None, "main", None, local_backend_type)
    mock_backend_instance.get_log_entries.assert_called_once_with(
        log_args=None,
        since=since_arg,
        until=None,
        author=None,
        me=False,
        grep=grep_arg,
        merged_only=False,
        include_paths=None,
        exclude_paths=None,
    )
    mock_build_commits_df.assert_called_once_with(MOCKED_GIT_LOG_ENTRIES)
    pd.testing.assert_frame_equal(df, MOCKED_DF)
