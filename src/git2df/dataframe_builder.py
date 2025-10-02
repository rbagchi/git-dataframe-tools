import pandas as pd
from typing import Dict, Any, List

def build_commits_df(parsed_data: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Converts parsed git data (from git_parser._parse_git_data_internal)
    into a Pandas DataFrame.

    Args:
        parsed_data: A dictionary where keys are author emails and values
                     are dictionaries containing 'name', 'added', 'deleted',
                     'total', 'commits' (set), and 'commit_hashes' (list).

    Returns:
        A Pandas DataFrame with commit-related information.
    """
    records = []
    for author_email, data in parsed_data.items():
        # For now, we'll create one record per author, summarizing their stats.
        # In a later step, we might expand this to one record per commit.
        records.append({
            'author_name': data['name'],
            'author_email': author_email,
            'added': data['added'],
            'deleted': data['deleted'],
            'total_diff': data['total'],
            'num_commits': len(data['commits']),
            'commit_hashes': data['commit_hashes'] # List of unique commit hashes
        })

    if not records:
        return pd.DataFrame(columns=['author_name', 'author_email', 'added', 'deleted', 'total_diff', 'num_commits', 'commit_hashes'])

    df = pd.DataFrame(records)
    return df
