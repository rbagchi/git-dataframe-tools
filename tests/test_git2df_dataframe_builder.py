import pandas as pd
from datetime import datetime, timezone
from git2df.dataframe_builder import build_commits_df

def test_build_commits_df_commit_centric():
    """Test build_commits_df with commit-centric parsed data."""
    parsed_data = [
        {
            'commit_hash': 'commit1hash',
            'parent_hash': 'parent1hash',
            'author_name': 'Author One',
            'author_email': 'author1@example.com',
            'commit_date': datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 1',
            'file_paths': 'file1.txt',
            'change_type': 'M',
            'additions': 10,
            'deletions': 5
        },
        {
            'commit_hash': 'commit1hash',
            'parent_hash': 'parent1hash',
            'author_name': 'Author One',
            'author_email': 'author1@example.com',
            'commit_date': datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 1',
            'file_paths': 'file2.py',
            'change_type': 'M',
            'additions': 2,
            'deletions': 1
        },
        {
            'commit_hash': 'commit2hash',
            'parent_hash': None,
            'author_name': 'Author Two',
            'author_email': 'author2@example.com',
            'commit_date': datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 2',
            'file_paths': 'file3.md',
            'change_type': 'A',
            'additions': 20,
            'deletions': 0
        },
        {
            'commit_hash': 'commit3hash',
            'parent_hash': 'parent3hash',
            'author_name': 'Author One',
            'author_email': 'author1@example.com',
            'commit_date': datetime(2023, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 3',
            'file_paths': 'file4.js',
            'change_type': 'D',
            'additions': 0,
            'deletions': 15
        },
    ]

    expected_df = pd.DataFrame(parsed_data)

    df = build_commits_df(parsed_data)

    pd.testing.assert_frame_equal(df, expected_df)

def test_build_commits_df_empty_input():
    """Test build_commits_df with empty parsed data."""
    parsed_data = []
    df = build_commits_df(parsed_data)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == [
        'commit_hash', 'parent_hash', 'author_name', 'author_email',
        'commit_date', 'commit_message', 'file_paths', 'change_type',
        'additions', 'deletions'
    ]