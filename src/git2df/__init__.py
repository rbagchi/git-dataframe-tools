import logging
import pandas as pd
from typing import Optional, List, Union

from git2df.backends import GitCliBackend
from git2df.dulwich_backend import DulwichRemoteBackend
from git2df.git_parser import _parse_git_data_internal
from git2df.dataframe_builder import build_commits_df

logger = logging.getLogger(__name__)


def _get_git_backend(
    repo_path: str,
    remote_url: Optional[str],
    remote_branch: str,
) -> Union[GitCliBackend, DulwichRemoteBackend]:
    """Factory function to get the appropriate Git backend."""
    if remote_url:
        return DulwichRemoteBackend(remote_url, remote_branch)
    else:
        return GitCliBackend(repo_path)


def get_commits_df(
    repo_path: str = ".",
    remote_url: Optional[str] = None,
    remote_branch: str = "main",
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
    logger.debug(
        f"get_commits_df called with: repo_path={repo_path}, remote_url={remote_url}, remote_branch={remote_branch}, since={since}, until={until}, author={author}, grep={grep}, merged_only={merged_only}, include_paths={include_paths}, exclude_paths={exclude_paths}"
    )

    default_log_args = [
        "--numstat",
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---",
        "--date=iso",
    ]

    if log_args is None:
        final_log_args = default_log_args
    else:
        # Prepend default args if custom args are provided, ensuring format is always present
        final_log_args = default_log_args + log_args

    backend = _get_git_backend(repo_path, remote_url, remote_branch)

    raw_log_output = backend.get_raw_log_output(
        log_args=final_log_args,
        since=since,
        until=until,
        author=author,
        grep=grep,
        merged_only=merged_only,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )

    # Split raw output into lines for the parser
    logger.debug(
        f"Raw log output from backend:\n{raw_log_output[:1000]}"
    )  # Log first 1000 chars
    log_lines = raw_log_output.splitlines()
    logger.debug(f"Received {len(log_lines)} raw log lines from Git.")

    parsed_entries = _parse_git_data_internal(log_lines)
    logger.debug(f"Parsed {len(parsed_entries)} GitLogEntry objects.")

    df = build_commits_df(parsed_entries)
    logger.info(f"Built DataFrame with {len(df)} rows.")

    return df
