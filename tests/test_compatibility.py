import pytest
import pandas as pd

from git_scoreboard.git_stats import parse_git_data, _prepare_author_data
from git_scoreboard.git_stats_pandas import parse_git_log_to_dataframe, get_author_stats_dataframe

def test_stats_compatibility():
    """Tests that git_stats and git_stats_pandas produce compatible output."""
    mock_git_data = """
commit_hash1|Author One|one@example.com|Commit message A
10	5	fileA.txt
2	1	fileB.txt

commit_hash2|Author Two|two@example.com|Commit message B
1	1	fileC.txt

commit_hash3|Author One|one@example.com|Commit message C
3	0	fileD.txt

commit_hash4|Author Three|three@example.com|Commit message D
15	7	fileE.txt

commit_hash5|Author One|one@example.com|Commit message E
1	1	fileF.txt
"""

    # --- Test original git_stats module ---
    original_authors_dict = parse_git_data(mock_git_data)
    original_author_list = _prepare_author_data(original_authors_dict)

    # Convert original output to DataFrame for easier comparison
    original_df = pd.DataFrame(original_author_list)
    original_df = original_df.rename(columns={'email': 'author_email', 'name': 'author_name'})
    original_df = original_df.sort_values(by='author_email').reset_index(drop=True)

    # Convert decile columns to nullable integer type for consistent comparison
    original_df['diff_decile'] = original_df['diff_decile'].astype(pd.Int64Dtype())
    original_df['commit_decile'] = original_df['commit_decile'].astype(pd.Int64Dtype())

    # --- Test git_stats_pandas module ---
    pandas_df_raw = parse_git_log_to_dataframe(mock_git_data)
    pandas_author_stats_df = get_author_stats_dataframe(pandas_df_raw)
    pandas_author_stats_df = pandas_author_stats_df.sort_values(by='author_email').reset_index(drop=True)

    # --- Compare outputs ---
    pandas_author_stats_df = pandas_author_stats_df[original_df.columns] # Reorder columns to match original_df
    pd.testing.assert_frame_equal(original_df, pandas_author_stats_df)
