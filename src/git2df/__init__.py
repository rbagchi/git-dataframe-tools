import pandas as pd
from typing import Optional, List

from git2df.backends import GitCliBackend
from git2df.git_parser import _parse_git_data_internal
from git2df.dataframe_builder import build_commits_df


def get_commits_df(
    repo_path: str = ".",
    log_args: Optional[List[str]] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    author: Optional[str] = None,
    grep: Optional[str] = None,
    merged_only: bool = False,
    include_paths: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Extracts git commit data from a repository and returns it as a Pandas DataFrame.

    Args:
        repo_path: The path to the git repository.
        log_args: Optional list of arguments to pass directly to 'git log'.
                  (e.g., ["--author=John Doe"])
        since: Optional string for --since argument (e.g., "1.month ago").
        until: Optional string for --until argument (e.g., "yesterday").
        author: Optional string to filter by author (e.g., "John Doe").
        grep: Optional string to filter by commit message (e.g., "fix").
        merged_only: If True, only include merged commits.
        include_paths: Optional list of paths to include.
        exclude_paths: Optional list of paths to exclude.

    Returns:
        A Pandas DataFrame containing commit information.
    """
    default_log_args = [
        "--numstat",
        "--pretty=format:--%H--%P--%an--%ae--%ad--%s",
        "--date=iso",
    ]

    if log_args is None:
        final_log_args = default_log_args
    else:
        # Prepend default args if custom args are provided, ensuring format is always present
        final_log_args = default_log_args + log_args

    backend = GitCliBackend()
    raw_log_output = backend.get_raw_log_output(
        repo_path,
        final_log_args,
        since=since,
        until=until,
        author=author,
        grep=grep,
        merged_only=merged_only,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )

    # Split raw output into lines for the parser
    log_lines = raw_log_output.splitlines()

    parsed_data = _parse_git_data_internal(log_lines)
    df = build_commits_df(parsed_data)

    return df
