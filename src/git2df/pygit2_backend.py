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
        last = repo.head.target

        since_dt, until_dt = get_date_filters(since, until)

        log_entries = []
        for commit in repo.walk(last, pygit2.GIT_SORT_TIME):
            commit_time = datetime.fromtimestamp(commit.author.time, tz=timezone.utc)

            if since_dt and commit_time < since_dt:
                break
            if until_dt and commit_time > until_dt:
                continue
            if author and author not in commit.author.name and author not in commit.author.email:
                continue
            if grep and grep not in commit.message:
                continue

            if commit.parents:
                diff = repo.diff(commit.parents[0], commit)
            else:
                diff = commit.tree.diff_to_tree()

            # Find similar files (renames and copies)
            diff.find_similar(flags=pygit2.enums.DiffFind.FIND_RENAMES | pygit2.enums.DiffFind.FIND_COPIES)

            file_changes = []
            for patch in diff:
                if patch.delta.status == pygit2.enums.DeltaStatus.RENAMED:
                    file_path = patch.delta.new_file.path
                elif patch.delta.status == pygit2.enums.DeltaStatus.DELETED:
                    file_path = patch.delta.old_file.path
                else:
                    file_path = patch.delta.new_file.path
                if isinstance(file_path, bytes):
                    file_path = file_path.decode('utf-8')

                if include_paths and not any(file_path.startswith(p) for p in include_paths):
                    continue
                if exclude_paths and any(file_path.startswith(p) for p in exclude_paths):
                    continue

                additions = patch.line_stats[1]
                deletions = patch.line_stats[2]

                current_change_type = patch.delta.status_char()
                if not commit.parents and current_change_type == 'D':
                    # This is an initial commit, and pygit2 reports additions as deletions
                    additions = patch.line_stats[2]  # Interpret deletions as additions
                    deletions = 0
                    final_change_type = 'A'
                else:
                    final_change_type = current_change_type

                file_changes.append(
                    FileChange(
                        file_path=file_path,
                        additions=additions,
                        deletions=deletions,
                        change_type=final_change_type,
                    )
                )
            
            if not file_changes and (include_paths or exclude_paths):
                continue

            log_entries.append(
                GitLogEntry(
                    commit_hash=str(commit.id),
                    parent_hash=str(commit.parent_ids[0]) if commit.parent_ids else None,
                    author_name=commit.author.name,
                    author_email=commit.author.email,
                    commit_date=commit_time,
                    commit_timestamp=commit.commit_time,
                    commit_message=commit.message.strip(),
                    file_changes=file_changes,
                )
            )
        logger.debug(f"Pygit2Backend.get_log_entries returning {len(log_entries)} entries.")
        return log_entries
