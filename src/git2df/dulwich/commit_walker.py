import datetime
import logging
from typing import List, Optional, cast

from dulwich.repo import Repo
from dulwich.objects import Commit
from dulwich.objects import Commit
from dulwich.objects import Commit
from tqdm import tqdm

from .commit_filters import DulwichCommitFilters
from .commit_formatter import DulwichCommitFormatter
from .diff_parser import DulwichDiffParser

logger = logging.getLogger(__name__)

class DulwichCommitWalker:
    """
    Walks through Dulwich commits, processes them, and formats the output.
    """

    def __init__(
        self,
        commit_filters: DulwichCommitFilters,
        commit_formatter: DulwichCommitFormatter,
    ):
        self.commit_filters = commit_filters
        self.commit_formatter = commit_formatter

    def _process_single_commit(
        self,
        repo: Repo,
        commit: Commit,
        author: Optional[str],
        grep: Optional[str],
        diff_parser: DulwichDiffParser,
    ) -> List[str]:
        commit_output_lines: List[str] = []

        logger.debug(
            f"--- Entered walker loop for commit: {commit.id.hex()} ---"
        )

        commit_metadata = self.commit_formatter.extract_commit_metadata(commit)
        logger.debug(
            f"Processing commit {commit_metadata['commit_hash']} with date {commit_metadata['commit_date']}"
        )

        if not self.commit_filters.filter_commits_by_author_and_grep(
            commit_metadata, author, grep
        ):
            return []

        commit_output_lines.append(
            self.commit_formatter.format_commit_line(commit_metadata)
        )
        logger.debug(f"Appended commit line for {commit_metadata['commit_hash']}")

        # Extract file changes
        old_tree_id = None
        if commit.parents:  # Not an initial commit


            parent_commit = cast(Commit, repo[commit.parents[0]])
            old_tree_id = parent_commit.tree

        file_changes = diff_parser.extract_file_changes(
            repo, commit, old_tree_id
        )
        logger.debug(f"Extracted file_changes for commit {commit.id.hex()}: {file_changes}")
        for file_change in file_changes:
            commit_output_lines.append(
                f"{file_change['additions']}\t{file_change['deletions']}\t{file_change['change_type']}\t{file_change['file_paths']}"
            )
        return commit_output_lines

    def _collect_and_filter_commits(
        self, repo: Repo, since_dt: Optional[datetime.datetime], until_dt: Optional[datetime.datetime]
    ) -> List[Commit]:
        all_commits = []
        logger.debug(f"Starting commit collection for repo: {repo.path}")
        for entry in repo.get_walker():
            commit: Commit = entry.commit
            logger.debug(f"Processing commit {commit.id.hex()} for date filtering.")

            commit_datetime = datetime.datetime.fromtimestamp(
                commit.commit_time, tz=datetime.timezone.utc
            )
            if not self.commit_filters.filter_commits_by_date(commit_datetime, since_dt, until_dt):
                logger.debug(f"Commit {commit.id.hex()} filtered out by date.")
                continue
            logger.debug(f"Commit {commit.id.hex()} passed date filter.")
            all_commits.append(commit)
        logger.debug(f"Finished commit collection. Found {len(all_commits)} commits after date filtering.")
        return all_commits

    def walk_commits(
        self,
        repo: Repo,
        since_dt: Optional[datetime.datetime],
        until_dt: Optional[datetime.datetime],
        author: Optional[str],
        grep: Optional[str],
        diff_parser: DulwichDiffParser,
        pbar: tqdm,
    ) -> str:
        output_lines: list[str] = []
        all_commits = self._collect_and_filter_commits(repo, since_dt, until_dt)

        # Update the total of the passed pbar for the parsing phase
        if not pbar.disable:
            pbar.total += len(all_commits)  # Add the number of commits to the total
        pbar.set_description("Parsing git log")  # Update description for parsing phase

        for commit in all_commits:
            pbar.update(1)
            commit_output = self._process_single_commit(
                repo, commit, author, grep, diff_parser
            )
            output_lines.extend(commit_output)

        logger.debug(f"Final output_lines: {output_lines}")
        return "\n".join(output_lines)
