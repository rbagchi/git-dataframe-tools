import datetime
import logging
from typing import List, Optional, cast
from git2df.git_parser import GitLogEntry

from dulwich.repo import Repo
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
        remote_branch: str,
    ):
        self.commit_filters = commit_filters
        self.commit_formatter = commit_formatter
        self.remote_branch = remote_branch

    def _get_commit_output_lines(
        self,
        repo: Repo,
        commit: Commit,
        author: Optional[str],
        grep: Optional[str],
        diff_parser: DulwichDiffParser,
    ) -> List[str]:
        commit_output_lines: List[str] = []

        commit_metadata = self.commit_formatter.extract_commit_metadata(commit)
        logger.debug(
            f"Processing commit {commit.id.hex()} (hash: {commit_metadata['commit_hash']}, date: {commit_metadata['commit_date']})"
        )

        if not self.commit_filters.filter_commits_by_author_and_grep(
            commit_metadata, author, grep
        ):
            logger.debug(f"Commit {commit.id.hex()} filtered out by author/grep.")
            return []

        commit_output_lines.append(
            self.commit_formatter.format_commit_line(commit_metadata)
        )

        old_tree_id = None
        if commit.parents:  # Not an initial commit

            parent_commit = cast(Commit, repo[commit.parents[0]])
            old_tree_id = parent_commit.tree

        file_changes = diff_parser.extract_file_changes(repo, commit, old_tree_id)
        logger.debug(
            f"Extracted {len(file_changes)} file changes for commit {commit.id.hex()}."
        )
        for file_change in file_changes:
            commit_output_lines.append(
                f"{file_change.additions}\t{file_change.deletions}\t{file_change.change_type}\t{file_change.file_path}"
            )
        return commit_output_lines

    def _process_all_filtered_commits(
        self,
        repo: Repo,
        all_commits: List[Commit],
        author: Optional[str],
        grep: Optional[str],
        diff_parser: DulwichDiffParser,
        pbar: tqdm,
    ) -> List[str]:
        output_lines: list[str] = []
        for commit in all_commits:
            pbar.update(1)
            commit_output = self._get_commit_output_lines(
                repo, commit, author, grep, diff_parser
            )
            output_lines.extend(commit_output)
        return output_lines

    def walk_commits(
        self,
        repo: Repo,
        since_dt: Optional[datetime.datetime],
        until_dt: Optional[datetime.datetime],
        author: Optional[str],
        grep: Optional[str],
        diff_parser: DulwichDiffParser,
        pbar: tqdm,
    ) -> List[GitLogEntry]:
        all_commits = self._collect_and_filter_commits(repo, since_dt, until_dt)

        self._initialize_progress_bar(pbar, all_commits)

        parsed_entries: List[GitLogEntry] = []
        for commit in all_commits:
            pbar.update(1)
            commit_metadata = self.commit_formatter.extract_commit_metadata(commit)

            if not self.commit_filters.filter_commits_by_author_and_grep(
                commit_metadata, author, grep
            ):
                logger.debug(f"Commit {commit.id.hex()} filtered out by author/grep.")
                continue

            old_tree_id = None
            if commit.parents:  # Not an initial commit
                try:
                    parent_commit = cast(Commit, repo[commit.parents[0]])
                    old_tree_id = parent_commit.tree
                except KeyError:
                    # This can happen if the parent commit is not in the local clone
                    # (e.g. shallow clone). We can't get file changes in this case.
                    logger.warning(f"Parent commit {commit.parents[0].hex()} not found for commit {commit.id.hex()}. Cannot determine file changes.")

            file_changes_list = diff_parser.extract_file_changes(repo, commit, old_tree_id)
            
            if (diff_parser.include_paths or diff_parser.exclude_paths) and not file_changes_list:
                logger.debug(f"Commit {commit.id.hex()} filtered out by path filters.")
                continue

            entry = GitLogEntry(
                commit_hash=commit_metadata["commit_hash"],
                parent_hash=commit_metadata["parent_hashes"],
                author_name=commit_metadata["author_name"],
                author_email=commit_metadata["author_email"],
                commit_date=commit_metadata["commit_date"],
                commit_timestamp=commit_metadata["commit_timestamp"],
                commit_message=commit_metadata["commit_message"],
                file_changes=file_changes_list,
            )
            parsed_entries.append(entry)

        logger.debug(f"Final parsed_entries: {parsed_entries}")
        return parsed_entries

    def _collect_and_filter_commits(
        self,
        repo: Repo,
        since_dt: Optional[datetime.datetime],
        until_dt: Optional[datetime.datetime],
    ) -> List[Commit]:
        all_commits = []
        logger.debug(f"Starting commit collection for repo: {repo.path}")
        print(f"DEBUG: repo.refs: {repo.refs}")
        # Explicitly get the head of the remote_branch (main) and walk from there
        try:
            main_branch_sha = repo.refs[f"refs/heads/{self.remote_branch}".encode("utf-8")]
            print(f"DEBUG: main_branch_sha: {main_branch_sha.hex()}")
        except KeyError:
            logger.warning(f"Branch {self.remote_branch} not found in repo {repo.path}. No commits to walk.")
            return []

        for entry in repo.get_walker(include=[main_branch_sha]):
            commit: Commit = entry.commit
            commit_datetime = datetime.datetime.fromtimestamp(
                commit.commit_time, tz=datetime.timezone.utc
            )

            if not self.commit_filters.filter_commits_by_date(
                commit_datetime, since_dt, until_dt
            ):
                logger.debug(
                    f"Commit {commit.id.hex()} (date: {commit_datetime}) filtered out by date."
                )
                continue

            all_commits.append(commit)
        logger.debug(
            f"Finished commit collection. Found {len(all_commits)} commits after date filtering."
        )
        return all_commits

    def _initialize_progress_bar(self, pbar: tqdm, all_commits: List[Commit]) -> None:
        """Initializes and updates the progress bar for commit processing."""
        if not pbar.disable:
            pbar.total += len(all_commits)  # Add the number of commits to the total
        pbar.set_description("Parsing git log")  # Update description for parsing phase
