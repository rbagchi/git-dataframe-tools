import logging
import os
from typing import List, Optional

from dulwich.repo import Repo

from ..backend_interface import GitBackend
from ..git_parser import GitLogEntry, parse_git_log
from .date_utils import get_date_filters
from .diff_parser import DulwichDiffParser
from .commit_filters import DulwichCommitFilters
from .commit_formatter import DulwichCommitFormatter
from .commit_walker import DulwichCommitWalker
from .repo_handler import DulwichRepoHandler

logger = logging.getLogger(__name__)


class DulwichRemoteBackend(GitBackend):
    """A backend for git2df that interacts with remote Git repositories using Dulwich."""

    def __init__(self, remote_url: str, remote_branch: str = "main"):
        self.remote_url = remote_url
        self.remote_branch = remote_branch
        self.is_local_repo = os.path.exists(remote_url) and os.path.isdir(remote_url)

        self.repo: Optional[Repo]

        if self.is_local_repo:
            self.repo = Repo(remote_url)
            logger.info(
                f"Using Dulwich backend for local repository at {remote_url}/{remote_branch}"
            )
        else:
            self.repo = None
            logger.info(
                f"Using Dulwich backend for remote operations on {remote_url}/{remote_branch}"
            )

        self.commit_filters = DulwichCommitFilters()
        self.commit_formatter = DulwichCommitFormatter()
        self.commit_walker = DulwichCommitWalker(
            self.commit_filters, self.commit_formatter
        )
        self.repo_handler = DulwichRepoHandler(
            self.remote_url,
            self.remote_branch,
            self.is_local_repo,
            self.repo,
            self.commit_walker,
        )

    def get_log_entries(
        self,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> List[GitLogEntry]:
        """
        Retrieves a list of GitLogEntry objects by calling get_raw_log_output
        and then parsing the result.
        """
        raw_output = self.get_raw_log_output(
            log_args=log_args,
            since=since,
            until=until,
            author=author,
            grep=grep,
            merged_only=merged_only,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
        )
        return parse_git_log(raw_output)

    def get_raw_log_output(
        self,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False,  # Not directly supported by dulwich fetch by date
        include_paths: Optional[List[str]] = None, # Will be filtered post-fetch
        exclude_paths: Optional[List[str]] = None,  # Will be filtered post-fetch
    ) -> str:
        """
        [DEPRECATED] Fetches git log information from a remote repository using Dulwich and returns it
        in a raw string format compatible with git2df's parser.
        Use get_log_entries instead.
        """
        since_dt, until_dt = get_date_filters(since, until)

        diff_parser = DulwichDiffParser(
            include_paths=include_paths, exclude_paths=exclude_paths
        )

        if self.is_local_repo:
            return self.repo_handler.handle_local_repo(
                since_dt, until_dt, author, grep, diff_parser
            )
        else:
            return self.repo_handler.handle_remote_repo(
                since_dt, until_dt, author, grep, diff_parser
            )
