import logging
import pandas as pd
from typing import Optional, List

from git2df.backend_interface import GitBackend
from git2df.backends import GitCliBackend
from git2df.dulwich.backend import DulwichRemoteBackend
from git2df.pygit2_backend import Pygit2Backend # Import Pygit2Backend
from git2df.dataframe_builder import build_commits_df
from git_dataframe_tools.git_repo_info_provider import GitRepoInfoProvider

logger = logging.getLogger(__name__)


def _get_git_backend(
    repo_path: str,
    remote_url: Optional[str],
    remote_branch: str,
    repo_info_provider: Optional[GitRepoInfoProvider] = None,
    local_backend_type: str = "cli", # New parameter for local backend selection
) -> GitBackend:
    """Factory function to get the appropriate Git backend."""
    if remote_url:
        return DulwichRemoteBackend(remote_url, remote_branch)
    else:
        if local_backend_type == "pygit2":
            return Pygit2Backend(repo_path)
        else: # Default to cli
            return GitCliBackend(repo_path, repo_info_provider=repo_info_provider)


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
    repo_info_provider: Optional[GitRepoInfoProvider] = None,
    local_backend_type: str = "cli", # New parameter for local backend selection
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
        repo_info_provider: Optional GitRepoInfoProvider instance for repository info.
        local_backend_type: Optional string to select the local backend type ('cli' or 'pygit2'). Defaults to 'cli'.

    Returns:
        A Pandas DataFrame containing commit information.
    """
    logger.debug(
        f"get_commits_df called with: repo_path={repo_path}, remote_url={remote_url}, remote_branch={remote_branch}, since={since}, until={until}, author={author}, grep={grep}, merged_only={merged_only}, include_paths={include_paths}, exclude_paths={exclude_paths}, repo_info_provider={repo_info_provider}, local_backend_type={local_backend_type}"
    )

    backend = _get_git_backend(repo_path, remote_url, remote_branch, repo_info_provider, local_backend_type)

    parsed_entries = backend.get_log_entries(
        log_args=log_args,
        since=since,
        until=until,
        author=author,
        grep=grep,
        merged_only=merged_only,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )
    logger.debug(f"Parsed {len(parsed_entries)} GitLogEntry objects.")

    df = build_commits_df(parsed_entries)
    logger.info(f"Built DataFrame with {len(df)} rows.")

    return df
