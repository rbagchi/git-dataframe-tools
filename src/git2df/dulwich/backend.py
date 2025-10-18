import logging
from typing import List, Optional
import subprocess

from dulwich.repo import Repo

from ..backend_interface import GitBackend
from ..git_parser import GitLogEntry
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

        self.repo: Optional[Repo] = None # Always treat as remote
        logger.info(
            f"Using Dulwich backend for remote operations on {remote_url}/{remote_branch}"
        )

        self.commit_filters = DulwichCommitFilters()
        self.commit_formatter = DulwichCommitFormatter()
        self.commit_walker = DulwichCommitWalker(
            self.commit_filters, self.commit_formatter, self.remote_branch
        )
        self.repo_handler = DulwichRepoHandler(
            self.remote_url,
            self.remote_branch,
            False, # Always treat as remote
            self.repo,
            self.commit_walker,
        )

    def get_log_entries(
        self,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        me: bool = False,
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> List[GitLogEntry]:
        """
        Retrieves a list of GitLogEntry objects directly from the Dulwich backend.
        """
        if author and me:
            raise ValueError("Cannot use both 'author' and 'me' filters together.")

        effective_author = author
        if me:
            try:
                # For remote backend, use local git config for '--me'
                user_name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, check=True).stdout.strip()
                user_email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, check=True).stdout.strip()
                if user_name or user_email:
                    effective_author = f"{user_name}|{user_email}"
                else:
                    logger.warning("'--me' was used, but Git user.name and user.email are not configured globally.")
            except Exception as e:
                logger.error(f"Error retrieving current Git user config for '--me': {e}")
                raise

        since_dt, until_dt = get_date_filters(since, until)

        diff_parser = DulwichDiffParser(
            include_paths=include_paths, exclude_paths=exclude_paths
        )

        return self.repo_handler.handle_remote_repo(
            since_dt, until_dt, effective_author, grep, diff_parser
        )

