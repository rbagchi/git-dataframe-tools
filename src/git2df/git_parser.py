import logging
import re
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


def _parse_git_data_internal(git_data: list[str]) -> list[dict]:
    """Parse git log data and extract commit details and file stats per commit."""
    logger.debug(f"Starting git log parsing for {len(git_data)} lines.")
    logger.debug(f"Received git_data:\n{git_data}")
    commits_data = []
    current_commit: Optional[dict[str, Any]] = None
    current_files: list[dict[str, Any]] = []

    # Wrap iteration with tqdm if available
    iterable_git_data = (
        tqdm(git_data, desc="Parsing git log") if TQDM_AVAILABLE else git_data
    )

    for i, line in enumerate(iterable_git_data):
        line = line.strip()
        logger.debug(f"Processing line {i+1}: '{line}'")

        if not line:
            # Empty line, usually separates commits or ends file stats
            if current_commit and current_files:
                logger.debug(f"End of commit block for {current_commit.get('commit_hash')}. Adding {len(current_files)} file changes.")
                # If we have a commit and files, add them to commits_data
                for file_info in current_files:
                    commit_record = current_commit.copy()
                    commit_record.update(file_info)
                    commits_data.append(commit_record)
                current_commit = None
                current_files = []
            else:
                logger.debug("Empty line encountered, but no current_commit or current_files to process.")
            continue

        if line.startswith("---"):
            # New commit entry
            if current_commit and current_files:
                logger.debug(f"Found new commit marker. Processing previous commit {current_commit.get('commit_hash')} with {len(current_files)} files.")
                # If we have a previous commit and its files, add them
                for file_info in current_files:
                    commit_record = current_commit.copy()
                    commit_record.update(file_info)
                    commits_data.append(commit_record)

            # Reset for the new commit
            logger.debug("Resetting for new commit.")
            current_commit = {}
            current_files = []

            parts = line.split("---")
            logger.debug(f"Commit marker parts: {parts}")
            # Expected format: ---%H---%P---%an---%ae---%ad---%s
            if len(parts) >= 7:
                commit_hash = parts[1]
                parent_hash = (
                    parts[2] if parts[2] else None
                )  # Parent hash can be empty for initial commit
                author_name = parts[3]
                author_email = parts[4]
                commit_date_str = parts[5]
                commit_message = parts[6]

                current_commit = {
                    "commit_hash": commit_hash,
                    "parent_hash": parent_hash,
                    "author_name": author_name,
                    "author_email": author_email,
                    "commit_date": datetime.fromisoformat(commit_date_str),
                    "commit_message": commit_message,
                }
                logger.debug(f"Parsed new commit: {current_commit}")
        else:
            # File stat line (format: added\tdeleted\tfilepath)
            if current_commit:
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
                    current_files.append(file_change)
                    logger.debug(f"Parsed file change: {file_change}")
                else:
                    logger.warning(f"Line did not match file stat pattern: '{line}'")
            else:
                logger.warning(f"File stat line encountered without current_commit: '{line}'")

    # Add the last commit's data if any
    if current_commit and current_files:
        logger.debug(f"Processing last commit {current_commit.get('commit_hash')} with {len(current_files)} files.")
        for file_info in current_files:
            commit_record = current_commit.copy()
            commit_record.update(file_info)
            commits_data.append(commit_record)

    logger.debug(
        f"Finished git log parsing. Total {len(commits_data)} file changes extracted."
    )
    logger.debug(f"Final commits_data: {commits_data}")
    return commits_data