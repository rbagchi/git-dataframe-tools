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
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> List[GitLogEntry]:
        """
        Retrieves a list of GitLogEntry objects directly from the Dulwich backend.
        """
        since_dt, until_dt = get_date_filters(since, until)

        diff_parser = DulwichDiffParser(
            include_paths=include_paths, exclude_paths=exclude_paths
        )

        return self.repo_handler.handle_remote_repo(
            since_dt, until_dt, author, grep, diff_parser
        )

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
        parsed_entries = self.get_log_entries(
            log_args=log_args,
            since=since,
            until=until,
            author=author,
            grep=grep,
            merged_only=merged_only,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
        )

        output_lines: List[str] = []
        for entry in parsed_entries:
            output_lines.append(self.commit_formatter.format_commit_line(entry.to_dict())) # Assuming to_dict() exists or similar
            for file_change in entry.file_changes:
                output_lines.append(
                    f"{file_change.additions}\t{file_change.deletions}\t{file_change.change_type}\t{file_change.file_path}"
                )
        return "\n".join(output_lines)
