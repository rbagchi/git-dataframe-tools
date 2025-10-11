import io
import logging
from typing import List, Optional
import dulwich.diff_tree
from dulwich.diff_tree import TreeChange
import dulwich.patch
from dulwich.objects import Commit
from dulwich.repo import Repo

logger = logging.getLogger(__name__)


class DulwichDiffParser:
    """
    Handles parsing of Dulwich diffs and tree changes to extract file modifications,
    additions, and deletions.
    """

    def __init__(
        self,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ):
        self.include_paths = include_paths
        self.exclude_paths = exclude_paths

    def _get_path_from_change(self, change: TreeChange) -> Optional[bytes]:
        # Path is in the 'new' entry for adds and modifies, and 'old' for deletes.
        if change.new and change.new.path:
            return change.new.path
        if change.old and change.old.path:
            return change.old.path
        return None

    def _should_include_path(self, path_str: str) -> bool:
        if self.include_paths and not any(
            path_str.startswith(p) for p in self.include_paths
        ):
            return False
        if self.exclude_paths and any(
            path_str.startswith(p) for p in self.exclude_paths
        ):
            return False
        return True

    @staticmethod
    def _get_change_type_char(change_type: str) -> str:
        if change_type == "add":
            return "A"
        elif change_type == "delete":
            return "D"
        elif change_type == "modify":
            return "M"
        return "U"  # Unknown

    def extract_file_changes(
        self,
        repo: Repo,
        commit: Commit,
        old_tree_id: Optional[bytes],
    ) -> List[dict]:
        file_changes = []

        for change in dulwich.diff_tree.tree_changes(
            repo.object_store, old_tree_id, commit.tree
        ):
            path = self._get_path_from_change(change)
            if not path:
                continue
            path_str = path.decode("utf-8")

            if not self._should_include_path(path_str):
                continue

            additions = 0
            deletions = 0
            change_type_char = self._get_change_type_char(change.type)

            if change.type == "add":
                assert change.new is not None
                try:
                    blob = repo.get_object(change.new.sha)
                    additions = len(blob.as_pretty_string().splitlines())
                except KeyError:
                    additions = 0 # Or handle as an error
            elif change.type == "delete":
                assert change.old is not None
                try:
                    blob = repo.get_object(change.old.sha)
                    deletions = len(blob.as_pretty_string().splitlines())
                except KeyError:
                    deletions = 0 # Or handle as an error
            elif change.type == "modify":
                if change.old and change.new:
                    # For modifications, we need to calculate the diff
                    patch_stream = io.BytesIO()
                    dulwich.patch.write_object_diff(
                        patch_stream,
                        repo.object_store,
                        change.old,
                        change.new,
                    )
                    patch_content = patch_stream.getvalue().decode("utf-8", errors="ignore")
                    for line in patch_content.splitlines():
                        if line.startswith("+") and not line.startswith("+++"):
                            additions += 1
                        elif line.startswith("-") and not line.startswith("---"):
                            deletions += 1

            change_type_char = self._get_change_type_char(change.type)

            file_changes.append(
                {
                    "file_paths": path_str,
                    "change_type": change_type_char,
                    "additions": additions,
                    "deletions": deletions,
                }
            )

        return file_changes

    def _parse_diff_output(self, diff_output: str) -> dict:
        line_stats = {}
        current_file_path = None
        current_additions = 0
        current_deletions = 0

        for line in diff_output.splitlines():
            if line.startswith("diff --git"):
                if current_file_path:
                    line_stats[current_file_path] = {
                        "additions": current_additions,
                        "deletions": current_deletions,
                    }
                current_file_path = None
                current_additions = 0
                current_deletions = 0

            elif line.startswith("--- a/"):
                pass
            elif line.startswith("+++ b/"):
                current_file_path = line[6:].strip()
            elif line.startswith("-") and not line.startswith("---"):
                current_deletions += 1
            elif line.startswith("+") and not line.startswith("+++"):
                current_additions += 1

        if current_file_path:
            line_stats[current_file_path] = {
                "additions": current_additions,
                "deletions": current_deletions,
            }
        return line_stats


