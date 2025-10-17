import pygit2
from datetime import datetime, timezone
from typing import List, Optional
import logging

from git2df.backend_interface import GitBackend
from git2df.git_parser import GitLogEntry, FileChange
from .date_utils import get_date_filters

logger = logging.getLogger(__name__)


class Pygit2Backend(GitBackend):
    """A backend for git2df that interacts with Git repositories using pygit2."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _is_merged_only_match(self, commit, merged_only: bool) -> bool:
        if merged_only and len(commit.parent_ids) <= 1:
            logger.debug(f"Commit {commit.id} excluded by merged_only filter: not a merge commit")
            return False
        return True

    def _is_since_dt_match(self, commit, commit_time: datetime, since_dt: Optional[datetime]) -> bool:
        if since_dt and commit_time < since_dt:
            logger.debug(f"Commit {commit.id} excluded by since_dt filter: {commit_time} < {since_dt}")
            return False
        return True

    def _is_until_dt_match(self, commit, commit_time: datetime, until_dt: Optional[datetime]) -> bool:
        if until_dt and commit_time > until_dt:
            logger.debug(f"Commit {commit.id} excluded by until_dt filter: {commit_time} > {until_dt}")
            return False
        return True

    def _is_author_match(self, commit, author: Optional[str]) -> bool:
        if author and author not in commit.author.name and author not in commit.author.email:
            return False
        return True

    def _is_grep_match(self, commit, grep: Optional[str]) -> bool:
        if grep and grep not in commit.message:
            return False
        return True

    def _commit_matches_filters(self, commit, since_dt, until_dt, author, grep, merged_only):
        commit_time = datetime.fromtimestamp(commit.committer.time, tz=timezone.utc) # Use committer time
        logger.debug(f"Commit hash: {commit.id}, Commit time: {commit_time}, Since date: {since_dt}, Until date: {until_dt}, Merged only: {merged_only}")

        if not self._is_merged_only_match(commit, merged_only):
            return False, False
        if not self._is_since_dt_match(commit, commit_time, since_dt):
            return False, True # False for match, True to break walk
        if not self._is_until_dt_match(commit, commit_time, until_dt):
            return False, False # False for match, False to continue walk
        if not self._is_author_match(commit, author):
            return False, False
        if not self._is_grep_match(commit, grep):
            return False, False
        return True, False # True for match, False to continue walk

    def _get_file_path_from_patch(self, patch):
        file_path = None
        if patch.delta.status == pygit2.enums.DeltaStatus.RENAMED:
            file_path = patch.delta.new_file.path
        elif patch.delta.status == pygit2.enums.DeltaStatus.DELETED:
            file_path = patch.delta.old_file.path
        else:
            file_path = patch.delta.new_file.path

        if isinstance(file_path, bytes):
            file_path = file_path.decode('utf-8')
        return file_path

    def _is_path_filtered(self, file_path, include_paths, exclude_paths):
        if include_paths and not any(file_path.startswith(p) for p in include_paths):
            return True
        if exclude_paths and any(file_path.startswith(p) for p in exclude_paths):
            return True
        return False

    def _get_change_stats(self, patch, commit_parents):
        additions = patch.line_stats[1]
        deletions = patch.line_stats[2]
        current_change_type = patch.delta.status_char()

        if not commit_parents and current_change_type == 'D':
            additions = patch.line_stats[2]
            deletions = 0
            final_change_type = 'A'
        else:
            final_change_type = current_change_type
        return additions, deletions, final_change_type


    def _process_commit_file_changes(self, repo, commit, include_paths, exclude_paths) -> List[FileChange]:
        file_changes = []
        if commit.parents:
            diff = repo.diff(commit.parents[0], commit)
        else:
            diff = commit.tree.diff_to_tree()

        diff.find_similar(flags=pygit2.enums.DiffFind.FIND_RENAMES | pygit2.enums.DiffFind.FIND_COPIES)

        for patch in diff:
            file_path = None
            old_file_path = None

            if patch.delta.status == pygit2.enums.DeltaStatus.RENAMED:
                old_file_path_raw = patch.delta.old_file.path
                file_path_raw = patch.delta.new_file.path
                old_file_path = old_file_path_raw.decode('utf-8') if isinstance(old_file_path_raw, bytes) else old_file_path_raw
                file_path = file_path_raw.decode('utf-8') if isinstance(file_path_raw, bytes) else file_path_raw
            elif patch.delta.status == pygit2.enums.DeltaStatus.DELETED:
                file_path_raw = patch.delta.old_file.path
                file_path = file_path_raw.decode('utf-8') if isinstance(file_path_raw, bytes) else file_path_raw
            else:
                file_path_raw = patch.delta.new_file.path
                file_path = file_path_raw.decode('utf-8') if isinstance(file_path_raw, bytes) else file_path_raw

            if self._is_path_filtered(file_path, include_paths, exclude_paths):
                continue

            additions, deletions, final_change_type = self._get_change_stats(patch, commit.parents)

            file_changes.append(
                FileChange(
                    file_path=file_path,
                    additions=additions,
                    deletions=deletions,
                    change_type=final_change_type,
                    old_file_path=old_file_path,
                )
            )
        return file_changes

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
        logger.debug(f"Pygit2Backend.get_log_entries called with repo_path={self.repo_path}")
        try:
            repo = pygit2.Repository(self.repo_path)
        except KeyError:
            logger.warning(f"No git repository found at {self.repo_path}")
            return []
        try:
            last = repo.head.target
        except pygit2.GitError as e:
            logger.warning(f"GitError accessing repo.head.target for {self.repo_path}: {e}. Assuming empty repository.")
            return []

        since_dt, until_dt = get_date_filters(since, until)

        log_entries = []
        for commit in repo.walk(last, pygit2.GIT_SORT_TIME):
            matches, should_break = self._commit_matches_filters(commit, since_dt, until_dt, author, grep, merged_only)
            if should_break:
                break
            if not matches:
                continue

            commit_time = datetime.fromtimestamp(commit.committer.time, tz=timezone.utc)

            file_changes = self._process_commit_file_changes(repo, commit, include_paths, exclude_paths)

            if not file_changes and (include_paths or exclude_paths):
                continue

            log_entries.append(
                GitLogEntry(
                    commit_hash=str(commit.id),
                    parent_hashes=[str(parent_id) for parent_id in commit.parent_ids],
                    author_name=commit.author.name,
                    author_email=commit.author.email,
                    commit_date=commit_time,
                    commit_timestamp=commit.committer.time,
                    commit_message=commit.message.strip(),
                    file_changes=file_changes,
                )
            )
        logger.debug(f"Pygit2Backend.get_log_entries returning {len(log_entries)} entries.")
        return log_entries
