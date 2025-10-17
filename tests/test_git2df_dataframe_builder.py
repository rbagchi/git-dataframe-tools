import pandas as pd
from datetime import datetime, timezone
from git2df.dataframe_builder import build_commits_df
from git2df.git_parser import GitLogEntry, FileChange


def test_build_commits_df_commit_centric():
    """Test build_commits_df with commit-centric parsed data."""
    # Prepare GitLogEntry objects from the original parsed_data structure
    # This simulates the output of the new _parse_git_data_internal
    commit1_date = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    commit2_date = datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc)
    commit3_date = datetime(2023, 1, 3, 12, 0, 0, tzinfo=timezone.utc)

    git_log_entries = [
        GitLogEntry(
            commit_hash="commit1hash",
            parent_hashes=["parent1hash"],
            author_name="Author One",
            author_email="author1@example.com",
            commit_date=commit1_date,
            commit_timestamp=1672531200,
            commit_message="Subject 1",
            file_changes=[
                FileChange("file1.txt", 10, 5, "M"),
                FileChange("file2.py", 2, 1, "M"),
            ],
        ),
        GitLogEntry(
            commit_hash="commit2hash",
            parent_hashes=[],
            author_name="Author Two",
            author_email="author2@example.com",
            commit_date=commit2_date,
            commit_timestamp=1672617600,
            commit_message="Subject 2",
            file_changes=[
                FileChange("file3.md", 20, 0, "A"),
            ],
        ),
        GitLogEntry(
            commit_hash="commit3hash",
            parent_hashes=["parent3hash"],
            author_name="Author One",
            author_email="author1@example.com",
            commit_date=commit3_date,
            commit_timestamp=1672704000,
            commit_message="Subject 3",
            file_changes=[
                FileChange("file4.js", 0, 15, "D"),
            ],
        ),
    ]

    # The expected DataFrame should be the same as before, but generated from the new structure
    expected_raw_data = [
        {
            "commit_hash": "commit1hash",
            "parent_hashes": ["parent1hash"],
            "author_name": "Author One",
            "author_email": "author1@example.com",
            "commit_date": commit1_date,
            "commit_timestamp": 1672531200,
            "commit_message": "Subject 1",
            "file_paths": "file1.txt",
            "change_type": "M",
            "additions": 10,
            "deletions": 5,
            "old_file_path": None,
        },
        {
            "commit_hash": "commit1hash",
            "parent_hash": "parent1hash",
            "author_name": "Author One",
            "author_email": "author1@example.com",
            "commit_date": commit1_date,
            "commit_timestamp": 1672531200,
            "commit_message": "Subject 1",
            "file_paths": "file2.py",
            "change_type": "M",
            "additions": 2,
            "deletions": 1,
            "old_file_path": None,
        },
        {
            "commit_hash": "commit2hash",
            "parent_hashes": [],
            "author_name": "Author Two",
            "author_email": "author2@example.com",
            "commit_date": commit2_date,
            "commit_timestamp": 1672617600,
            "commit_message": "Subject 2",
            "file_paths": "file3.md",
            "change_type": "A",
            "additions": 20,
            "deletions": 0,
            "old_file_path": None,
        },
        {
            "commit_hash": "commit3hash",
            "parent_hashes": ["parent3hash"],
            "author_name": "Author One",
            "author_email": "author1@example.com",
            "commit_date": commit3_date,
            "commit_timestamp": 1672704000,
            "commit_message": "Subject 3",
            "file_paths": "file4.js",
            "change_type": "D",
            "additions": 0,
            "deletions": 15,
            "old_file_path": None,
        },
    ]
    expected_df = pd.DataFrame(expected_raw_data)

    df = build_commits_df(git_log_entries)

    pd.testing.assert_frame_equal(df, expected_df)


def test_build_commits_df_empty_input():
    """Test build_commits_df with empty parsed data."""
    parsed_data = []
    df = build_commits_df(parsed_data)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == [
        "commit_hash",
        "parent_hashes",
        "author_name",
        "author_email",
        "commit_date",
        "commit_timestamp",
        "commit_message",
        "file_paths",
        "change_type",
        "additions",
        "deletions",
        "old_file_path",
    ]
