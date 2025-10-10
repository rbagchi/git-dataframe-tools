import logging
import re
from datetime import datetime
from typing import Any, Optional
import sys

logger = logging.getLogger(__name__)

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


def _parse_git_data_internal(git_data: list[str]) -> list[dict]:
    """Parse git log data and extract commit details and file stats per commit."""
    commits_data = []
    current_commit_metadata: Optional[dict[str, Any]] = None
    current_commit_files: list[dict[str, Any]] = []

    # Wrap iteration with tqdm if available
    iterable_git_data = (
        tqdm(git_data, desc="Parsing git log", disable=not sys.stdout.isatty())
        if TQDM_AVAILABLE
        else git_data
    )

    for i, line in enumerate(iterable_git_data):
        line = line.strip()

        if line.startswith("@@@COMMIT@@@"):
            # If we have a previous commit's data, process it before starting a new one
            if current_commit_metadata:
                if current_commit_files:
                    for file_info in current_commit_files:
                        commit_record = current_commit_metadata.copy()
                        commit_record.update(file_info)
                        commits_data.append(commit_record)
                else:
                    # Commit with no file changes (e.g., merge commits with --numstat)
                    commits_data.append(current_commit_metadata.copy())

            # Reset for the new commit
            current_commit_metadata = {}
            current_commit_files = []

            parts = line.split("@@@FIELD@@@")
            # Expected format: @@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad@@@FIELD@@@%s
            # The first part will be "@@@COMMIT@@@<commit_hash>", so we need at least 6 fields + the initial marker
            if len(parts) >= 6:
                commit_hash_with_marker = parts[0]
                commit_hash = commit_hash_with_marker.replace("@@@COMMIT@@@", "") # Extract hash

                parent_hash = (
                    parts[1] if parts[1] else None
                )  # Parent hash can be empty for initial commit
                author_name = parts[2]
                author_email = parts[3]
                commit_date_str = parts[4]
                commit_message = parts[5]

                current_commit_metadata = {
                    "commit_hash": commit_hash,
                    "parent_hash": parent_hash,
                    "author_name": author_name,
                    "author_email": author_email,
                    "commit_date": datetime.fromisoformat(commit_date_str),
                    "commit_message": commit_message,
                }
            else:
                logger.warning(f"Commit line did not match expected pattern: '{line}'")
                current_commit_metadata = None # Explicitly set to None if parsing fails
        elif not line:
            # Empty line signifies end of file stats for the current commit.
            # No action needed here, as processing happens when a new commit starts
            # or at the end of the loop.
            pass
        else:  # File stat line (format: added\\tdeleted\\tfilepath)
            if current_commit_metadata:
                stat_match = re.match(r"^(\d+|-)\s+(\d+|-)\s+(.+)$", line)
                if stat_match:
                    added_str, deleted_str, file_path = stat_match.groups()

                    additions = 0 if added_str == "-" else int(added_str)
                    deletions = 0 if deleted_str == "-" else int(deleted_str)

                    # Determine change_type (simplified for now, can be expanded)
                    change_type = "M"  # Modified by default
                    if additions > 0 and deletions == 0:
                        change_type = "A"  # Added
                    elif additions == 0 and deletions > 0:
                        change_type = "D"  # Deleted
                    # 'R' for rename, 'C' for copy are harder to get with --numstat alone

                    file_change = {
                        "file_paths": file_path,
                        "change_type": change_type,
                        "additions": additions,
                        "deletions": deletions,
                    }
                    current_commit_files.append(file_change)
                else:
                    logger.warning(f"Line did not match file stat pattern: '{line}'")
            else:
                logger.warning(
                    f"File stat line encountered without current_commit_metadata: '{line}'"
                )

    # Process the last commit's data if any
    if current_commit_metadata:
        if current_commit_files:
            for file_info in current_commit_files:
                commit_record = current_commit_metadata.copy()
                commit_record.update(file_info)
                commits_data.append(commit_record)
        else:
            commits_data.append(current_commit_metadata.copy())

    return commits_data
