import pandas as pd
from collections import defaultdict
from git2df.dataframe_builder import build_commits_df

def test_build_commits_df_basic():
    """Test build_commits_df with basic parsed data."""
    parsed_data = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set(),
        'commit_hashes': []
    })

    parsed_data['author1@example.com'] = {
        'name': 'Author One',
        'added': 10,
        'deleted': 5,
        'total': 15,
        'commits': {'hash1', 'hash2'},
        'commit_hashes': ['hash1', 'hash2']
    }
    parsed_data['author2@example.com'] = {
        'name': 'Author Two',
        'added': 20,
        'deleted': 10,
        'total': 30,
        'commits': {'hash3'},
        'commit_hashes': ['hash3']
    }

    df = build_commits_df(parsed_data)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['author_name', 'author_email', 'added', 'deleted', 'total_diff', 'num_commits', 'commit_hashes']

    # Verify data for Author One
    author_one_row = df[df['author_email'] == 'author1@example.com'].iloc[0]
    assert author_one_row['author_name'] == 'Author One'
    assert author_one_row['added'] == 10
    assert author_one_row['deleted'] == 5
    assert author_one_row['total_diff'] == 15
    assert author_one_row['num_commits'] == 2
    assert sorted(author_one_row['commit_hashes']) == sorted(['hash1', 'hash2'])

    # Verify data for Author Two
    author_two_row = df[df['author_email'] == 'author2@example.com'].iloc[0]
    assert author_two_row['author_name'] == 'Author Two'
    assert author_two_row['added'] == 20
    assert author_two_row['deleted'] == 10
    assert author_two_row['total_diff'] == 30
    assert author_two_row['num_commits'] == 1
    assert sorted(author_two_row['commit_hashes']) == sorted(['hash3'])

def test_build_commits_df_empty_input():
    """Test build_commits_df with empty parsed data."""
    parsed_data = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set(),
        'commit_hashes': []
    })

    df = build_commits_df(parsed_data)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == ['author_name', 'author_email', 'added', 'deleted', 'total_diff', 'num_commits', 'commit_hashes']
