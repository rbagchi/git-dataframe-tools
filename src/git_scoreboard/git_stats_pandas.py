import pandas as pd
import re
import math
from .scoreboard import GitAnalysisConfig

def parse_git_log_to_dataframe(git_data: str) -> pd.DataFrame:
    """Parses raw git log --numstat output into a Pandas DataFrame."""
    lines = git_data.splitlines()
    data = []
    current_commit_info = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Commit info line: hash|author_name|author_email|subject
        if '|' in line and len(line.split('|')) >= 4:
            parts = line.split('|')
            current_commit_info = {
                'commit_hash': parts[0],
                'author_name': parts[1],
                'author_email': parts[2],
                'commit_message': parts[3]
            }
        # File stat line: added\tdeleted\tfilepath
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
        return pd.DataFrame(columns=['commit_hash', 'author_name', 'author_email', 'commit_message', 'added', 'deleted', 'filepath'])

    df = pd.DataFrame(data)
    return df

def get_author_stats_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates author statistics (added, deleted, total, commits, ranks, deciles)
    from a DataFrame of git log data.
    """
    if df.empty:
        return pd.DataFrame(columns=['author_name', 'author_email', 'added', 'deleted', 'total', 'commits', 'rank', 'diff_decile', 'commit_decile'])

    # Aggregate by author
    author_stats = df.groupby(['author_email', 'author_name']).agg(
        added=('added', 'sum'),
        deleted=('deleted', 'sum'),
        commits=('commit_hash', 'nunique')
    ).reset_index()

    author_stats['total'] = author_stats['added'] + author_stats['deleted']

    # Calculate ranks for total diff
    author_stats['rank'] = author_stats['total'].rank(method='min', ascending=False).astype(int)
    
    # Calculate diff deciles
    # qcut requires at least 2 unique values for quantiles. If not enough, handle gracefully.
    author_stats['diff_decile'] = author_stats['rank'].apply(lambda x: min(10, math.ceil(x * 10 / len(author_stats))))

    # Calculate commit deciles
    author_stats['commit_decile'] = author_stats['rank'].apply(lambda x: min(10, math.ceil(x * 10 / len(author_stats))))

    # Sort by total diff size (descending) for consistent output order
    author_stats = author_stats.sort_values(by='total', ascending=False).reset_index(drop=True)

    return author_stats

def find_author_stats_pandas(author_stats_df: pd.DataFrame, author_query: str) -> pd.DataFrame:
    """
    Finds and returns stats for a specific author from the author statistics DataFrame.
    """
    if author_stats_df.empty:
        return pd.DataFrame()

    query_lower = author_query.lower()
    matches_df = author_stats_df[
        author_stats_df['author_name'].str.lower().str.contains(query_lower) |
        author_stats_df['author_email'].str.lower().str.contains(query_lower)
    ]
    return matches_df

def print_ranking_pandas(author_stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the author statistics DataFrame sorted by total diff for printing.
    """
    if author_stats_df.empty:
        return pd.DataFrame()
    return author_stats_df.sort_values(by='total', ascending=False).reset_index(drop=True)
