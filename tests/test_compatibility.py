import pytest
import pandas as pd
import re

from git_scoreboard.git_stats import parse_git_log as parse_git_log_original
from git_scoreboard.git_stats_pandas import parse_git_log as parse_git_log_pandas

def _mock_git_data_to_df(mock_git_data_lines: list[str]) -> pd.DataFrame:
    """Helper to convert mock git log string to a DataFrame similar to git2df output."""
    lines = mock_git_data_lines
    data = []
    current_commit_info = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('--'):
            parts = line.split('--')
            if len(parts) >= 5:
                current_commit_info = {
                    'hash': parts[1],
                    'author_name': parts[2],
                    'author_email': parts[3],
                    'message': parts[4]
                }
        else:
            stat_match = re.match(r'^(\d+|-)\t(\d+|-)\t(.+)$', line)
            if stat_match and current_commit_info:
                added_str, deleted_str, filepath = stat_match.groups()
                
                added = 0 if added_str == '-' else int(added_str)
                deleted = 0 if deleted_str == '-' else int(deleted_str)
                
                row = current_commit_info.copy()
                row.update({
                    'added': added,
                    'deleted': deleted,
                    'filepath': filepath
                })
                data.append(row)
    
    if not data:
        return pd.DataFrame(columns=['hash', 'author_name', 'author_email', 'message', 'added', 'deleted', 'filepath'])

    df = pd.DataFrame(data)
    return df

def test_stats_compatibility():
    """Tests that git_stats and git_stats_pandas produce compatible output."""
    mock_git_data_str = """
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
    mock_df_for_original = _mock_git_data_to_df(mock_git_data_str.splitlines())
    original_author_list = parse_git_log_original(mock_df_for_original)

    # Convert original output to DataFrame for easier comparison
    original_df = pd.DataFrame(original_author_list)
    original_df = original_df.sort_values(by='author_email').reset_index(drop=True)

    # Convert decile columns to nullable integer type for consistent comparison
    original_df['diff_decile'] = original_df['diff_decile'].astype('int64')
    original_df['commit_decile'] = original_df['commit_decile'].astype('int64')

    # --- Test git_stats_pandas module ---
    mock_df_for_pandas = _mock_git_data_to_df(mock_git_data_str.splitlines())
    pandas_author_list = parse_git_log_pandas(mock_df_for_pandas)
    pandas_df = pd.DataFrame(pandas_author_list)
    pandas_df = pandas_df.sort_values(by='author_email').reset_index(drop=True)

    # --- Compare outputs ---
    pandas_df = pandas_df[original_df.columns] # Reorder columns to match original_df
    pd.testing.assert_frame_equal(original_df, pandas_df)
