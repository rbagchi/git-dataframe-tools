import pandas as pd
from typing import Optional, List, Dict, Any

from git2df.backends import GitCliBackend
from git2df.git_parser import _parse_git_data_internal
from git2df.dataframe_builder import build_commits_df

def get_commits_df(repo_path: str, log_args: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Extracts git commit data from a repository and returns it as a Pandas DataFrame.

    Args:
        repo_path: The path to the git repository.
        log_args: Optional list of arguments to pass directly to 'git log'.
                  (e.g., ["--since=1.month", "--author=John Doe"])

    Returns:
        A Pandas DataFrame containing commit information.
    """
    default_log_args = [
        '--numstat',
        '--pretty=format:--%H--%an--%ae--%ad--%s',
        '--date=iso'
    ]

    if log_args is None:
        log_args = default_log_args
    else:
        # Prepend default args if custom args are provided, ensuring format is always present
        log_args = default_log_args + log_args

    backend = GitCliBackend()
    raw_log_output = backend.get_raw_log_output(repo_path, log_args)
    
    # Split raw output into lines for the parser
    log_lines = raw_log_output.splitlines()

    parsed_data = _parse_git_data_internal(log_lines)
    df = build_commits_df(parsed_data)
    
    return df
