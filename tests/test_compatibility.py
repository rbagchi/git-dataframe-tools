import pytest
import pandas as pd

from git_scoreboard.git_stats import parse_git_log
from git_scoreboard.git_stats_pandas import parse_git_log

def test_stats_compatibility():
    """Tests that git_stats and git_stats_pandas produce compatible output."""
    mock_git_data = """
--commit_hash1--Author One--one@example.com--Commit message A
10	5	fileA.txt
2	1	fileB.txt

--commit_hash2--Author Two--two@example.com--Commit message B
1	1	fileC.txt

--commit_hash3--Author One--one@example.com--Commit message C
3	0	fileD.txt

--commit_hash4--Author Three--three@example.com--Commit message D
15	7	fileE.txt

--commit_hash5--Author One--one@example.com--Commit message E
1	1	fileF.txt
"""

    # --- Test original git_stats module ---
    original_author_list = parse_git_log(mock_git_data.splitlines())

    # Convert original output to DataFrame for easier comparison
    original_df = pd.DataFrame(original_author_list)
    original_df = original_df.sort_values(by='author_email').reset_index(drop=True)

    # Convert decile columns to nullable integer type for consistent comparison
    original_df['diff_decile'] = original_df['diff_decile'].astype('int64')
    original_df['commit_decile'] = original_df['commit_decile'].astype('int64')

    # --- Test git_stats_pandas module ---
    pandas_author_list = parse_git_log(mock_git_data.splitlines())
    pandas_df = pd.DataFrame(pandas_author_list)
    pandas_df = pandas_df.sort_values(by='author_email').reset_index(drop=True)

    # --- Compare outputs ---
    pandas_df = pandas_df[original_df.columns] # Reorder columns to match original_df
    pd.testing.assert_frame_equal(original_df, pandas_df)
