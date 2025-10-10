import pandas as pd
from unittest.mock import patch, MagicMock
from git2df import get_commits_df
from datetime import datetime, timezone

# Mock data for commit-centric output
MOCKED_RAW_LOG_OUTPUT = [
    "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00@@@FIELD@@@Subject 1",
    "10\t5\tfile1.txt",
    "",
    "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T11:00:00+00:00@@@FIELD@@@Subject 2",
    "20\t0\tfile2.py",
]

MOCKED_PARSED_DATA_RAW_BLOCKS = [
    [
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00@@@FIELD@@@Subject 1",
        "10\t5\tfile1.txt",
    ],
    [
        "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T11:00:00+00:00@@@FIELD@@@Subject 2",
        "20\t0\tfile2.py",
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

from git2df.git_parser import GitLogEntry, FileChange

MOCKED_GIT_LOG_ENTRIES = [
    GitLogEntry(
        commit_hash="commit1hash",
        parent_hash="parent1hash",
        author_name="Author One",
        author_email="author1@example.com",
        commit_date=datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        commit_message="Subject 1",
        file_changes=[
            FileChange("file1.txt", 10, 5, "M"),
        ],
    ),
    GitLogEntry(
        commit_hash="commit2hash",
        parent_hash=None,
        author_name="Author Two",
        author_email="author2@example.com",
        commit_date=datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
        commit_message="Subject 2",
        file_changes=[
            FileChange("file2.py", 20, 0, "A"),
        ],
    ),
]

MOCKED_DF = pd.DataFrame(MOCKED_PARSED_DATA)


@patch("git2df.build_commits_df")
@patch("git2df._parse_git_data_internal")
@patch("git2df.GitCliBackend")
@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
def test_get_commits_df_with_filters(
    mock_get_default_branch,
    mock_git_cli_backend,
    mock_parse_git_data_internal,
    mock_build_commits_df,
):
    # Setup mocks
    mock_backend_instance = MagicMock()
    mock_git_cli_backend.return_value = mock_backend_instance
    mock_backend_instance.get_raw_log_output.return_value = "\n".join(
        MOCKED_RAW_LOG_OUTPUT
    )

    mock_parse_git_data_internal.return_value = MOCKED_GIT_LOG_ENTRIES
    mock_build_commits_df.return_value = MOCKED_DF

    repo_path = "/test/another_repo"
    since_arg = "2.weeks"
    grep_arg = "feature"

    # Call the function under test
    df = get_commits_df(repo_path, since=since_arg, grep=grep_arg)

    # Assertions
    mock_git_cli_backend.assert_called_once_with()
    mock_backend_instance.get_raw_log_output.assert_called_once_with(
        repo_path=repo_path,
                    log_args=[
                        "--numstat",
                        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad@@@FIELD@@@%s",
                        "--date=iso",
                    ],
                    since=since_arg,
                    until=None,        author=None,
        grep=grep_arg,
        merged_only=False,
        include_paths=None,
        exclude_paths=None,
    )
    mock_parse_git_data_internal.assert_called_once_with(MOCKED_RAW_LOG_OUTPUT)
    mock_build_commits_df.assert_called_once_with(MOCKED_GIT_LOG_ENTRIES)
    pd.testing.assert_frame_equal(df, MOCKED_DF)
