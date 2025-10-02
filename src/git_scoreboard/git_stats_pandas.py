import pandas as pd
import re
import math
from .config_models import GitAnalysisConfig

def _calculate_decile_from_rank(rank, n):
    return min(10, math.ceil(rank * 10 / n))

def _parse_git_log_to_dataframe_internal(git_data: list[str]) -> pd.DataFrame:
    """Parses raw git log --numstat output into a Pandas DataFrame."""
    lines = git_data
    data = []
    current_commit_info = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Commit info line: hash|author_name|author_email|subject
        if line.startswith('--'):
            parts = line.split('--')
            if len(parts) >= 5:
                current_commit_info = {
                    'commit_hash': parts[1],
                    'author_name': parts[2],
                    'author_email': parts[3],
                    'commit_message': parts[4]
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

def parse_git_log(git_data: list[str]) -> list[dict]:
    """Parses raw git log data using pandas and prepares author statistics."""
    df = _parse_git_log_to_dataframe_internal(git_data)
    author_stats_df = _get_author_stats_dataframe_internal(df)
    return author_stats_df.to_dict(orient='records')

def _get_author_stats_dataframe_internal(df: pd.DataFrame) -> pd.DataFrame:
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

    if author_stats.empty:
        return pd.DataFrame(columns=['author_name', 'author_email', 'added', 'deleted', 'total', 'commits', 'rank', 'diff_decile', 'commit_decile'])

    author_stats['total'] = author_stats['added'] + author_stats['deleted']

    # Calculate ranks for total diff
    author_stats['rank'] = author_stats['total'].rank(method='min', ascending=False).astype(int)

    # Calculate diff_decile
    author_stats_diff_sorted = author_stats.sort_values(by='total', ascending=False).reset_index(drop=True)
    n_diff = len(author_stats_diff_sorted)
    if n_diff > 0:
        current_decile_diff = 1
        for i in range(n_diff):
            if i > 0 and author_stats_diff_sorted.loc[i, 'total'] < author_stats_diff_sorted.loc[i-1, 'total']:
                current_rank_diff = i + 1
                current_decile_diff = min(10, math.ceil(current_rank_diff * 10 / n_diff))
            author_stats_diff_sorted.loc[i, 'diff_decile'] = int(current_decile_diff)
    else:
        author_stats_diff_sorted['diff_decile'] = pd.Series(dtype=pd.Int64Dtype())

    # Calculate commit_decile
    author_stats_commit_sorted = author_stats.sort_values(by='commits', ascending=False).reset_index(drop=True)
    n_commit = len(author_stats_commit_sorted)
    if n_commit > 0:
        current_decile_commit = 1
        for i in range(n_commit):
            if i > 0 and author_stats_commit_sorted.loc[i, 'commits'] < author_stats_commit_sorted.loc[i-1, 'commits']:
                current_rank_commit = i + 1
                current_decile_commit = min(10, math.ceil(current_rank_commit * 10 / n_commit))
            author_stats_commit_sorted.loc[i, 'commit_decile'] = int(current_decile_commit)
    else:
        author_stats_commit_sorted['commit_decile'] = pd.Series(dtype=pd.Int64Dtype())

    # Merge diff_decile back to the original author_stats DataFrame
    author_stats = author_stats.merge(
        author_stats_diff_sorted[['author_email', 'diff_decile']],
        on='author_email',
        how='left'
    )

    # Merge commit_decile back to the original author_stats DataFrame
    author_stats = author_stats.merge(
        author_stats_commit_sorted[['author_email', 'commit_decile']],
        on='author_email',
        how='left'
    )

    # Ensure decile columns are of Int64Dtype after merge
    author_stats['diff_decile'] = author_stats['diff_decile'].astype(pd.Int64Dtype())
    author_stats['commit_decile'] = author_stats['commit_decile'].astype(pd.Int64Dtype())

    # Sort by total diff size (descending) for consistent output order
    author_stats = author_stats.sort_values(by='total', ascending=False).reset_index(drop=True)

    if author_stats.empty:
        return pd.DataFrame(columns=['author_name', 'author_email', 'added', 'deleted', 'total', 'commits', 'rank', 'diff_decile', 'commit_decile'])

    return author_stats

def find_author_stats(author_stats: list[dict], author_query: str) -> list[dict]:
    """
    Finds and returns stats for a specific author from the author statistics list.
    """
    if not author_stats:
        return []

    query_lower = author_query.lower()
    matches = []
    for author in author_stats:
        if (query_lower in author['author_name'].lower() or 
            query_lower in author['author_email'].lower()):
            matches.append(author)
    return matches

def get_ranking(author_stats: list[dict]) -> list[dict]:
    """
    Returns the author statistics list sorted by total diff for printing.
    """
    if not author_stats:
        return []
    return sorted(author_stats, key=lambda x: x['total'], reverse=True)