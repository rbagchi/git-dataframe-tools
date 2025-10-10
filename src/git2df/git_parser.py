import logging
import re
from datetime import datetime
from typing import Any, Optional, List, Dict
import sys
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


@dataclass
class FileChange:
    file_path: str
    additions: int
    deletions: int
    change_type: str


@dataclass
class GitLogEntry:
    commit_hash: str
    parent_hash: Optional[str]
    author_name: str
    author_email: str
    commit_date: datetime
    commit_timestamp: int
    commit_message: str
    file_changes: List[FileChange] = field(default_factory=list)


def _parse_commit_metadata_line(line: str) -> Optional[Dict[str, Any]]:
    """Parses a single commit metadata line and returns a dictionary of its components."""
    if not line.startswith("@@@COMMIT@@@"):
        return None

    parts = line.split("@@@FIELD@@@")
    # Expected format: @@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@%B
    if len(parts) < 6:
        logger.warning(f"Malformed commit metadata line: '{line}'")
        return None

    commit_hash_with_marker = parts[0]
    commit_hash = commit_hash_with_marker.replace("@@@COMMIT@@@", "")

    parent_hash = parts[1] if parts[1] else None
    author_name = parts[2]
    author_email = parts[3]
    
    date_timestamp_str = parts[4]
    raw_commit_message_part = parts[5]

    # Extract commit message using the new delimiters
    msg_start_idx = raw_commit_message_part.find("---MSG_START---")
    msg_end_idx = raw_commit_message_part.find("---MSG_END---")

    if msg_start_idx != -1 and msg_end_idx != -1 and msg_start_idx < msg_end_idx:
        commit_message = raw_commit_message_part[msg_start_idx + len("---MSG_START---"):msg_end_idx]
    else:
        logger.warning(f"Could not find commit message delimiters in: '{raw_commit_message_part}'")
        commit_message = raw_commit_message_part # Fallback to raw part if delimiters not found

    try:
        commit_date_str, commit_timestamp_str = date_timestamp_str.split('\t')
        commit_date = datetime.fromisoformat(commit_date_str)
        commit_timestamp = int(commit_timestamp_str)
    except ValueError:
        logger.warning(
            f"Could not parse commit date or timestamp: '{date_timestamp_str}' in line '{line}'"
        )
        return None

    return {
        "commit_hash": commit_hash,
        "parent_hash": parent_hash,
        "author_name": author_name,
        "author_email": author_email,
        "commit_date": commit_date,
        "commit_timestamp": commit_timestamp,
        "commit_message": commit_message,
    }


def _parse_file_stat_line(line: str) -> Optional[FileChange]:
    """Parses a single file statistics line and returns a FileChange object."""
    stat_match = re.match(r"^(\d+|-)\s+(\d+|-)\s+(?:([ADMT])\s+)?(.+)$", line)
    if not stat_match:
        logger.warning(f"Line did not match file stat pattern: '{line}'")
        return None

    added_str, deleted_str, change_type_match, file_path = stat_match.groups()

    change_type = change_type_match if change_type_match else "M"  # Default to 'M' if not explicitly provided

    additions = 0 if added_str == "-" else int(added_str)
    deletions = 0 if deleted_str == "-" else int(deleted_str)

    return FileChange(
        file_path=file_path,
        additions=additions,
        deletions=deletions,
        change_type=change_type,
    )


def _process_raw_commit_block(raw_block: List[str]) -> Optional[GitLogEntry]:
    """Processes a single raw commit block (list of strings) into a GitLogEntry object."""
    if not raw_block:
        return None

    commit_metadata_dict = _parse_commit_metadata_line(raw_block[0])
    if not commit_metadata_dict:
        return None

    file_changes: List[FileChange] = []
    for line in raw_block[1:]:
        file_change = _parse_file_stat_line(line)
        if file_change:
            file_changes.append(file_change)

    return GitLogEntry(
        commit_hash=commit_metadata_dict["commit_hash"],
        parent_hash=commit_metadata_dict["parent_hash"],
        author_name=commit_metadata_dict["author_name"],
        author_email=commit_metadata_dict["author_email"],
        commit_date=commit_metadata_dict["commit_date"],
        commit_timestamp=commit_metadata_dict["commit_timestamp"],
        commit_message=commit_metadata_dict["commit_message"],
        file_changes=file_changes,
    )


def _parse_git_data_internal(git_data: list[str]) -> List[GitLogEntry]:
    """Parses raw git log data into GitLogEntry objects."""
    raw_commit_blocks: List[List[str]] = []
    current_block: List[str] = []

    # First pass: collect raw commit blocks
    iterable_git_data_collect = (
        tqdm(
            git_data,
            desc="Collecting raw commit blocks",
            disable=not sys.stdout.isatty(),
        )
        if TQDM_AVAILABLE
        else git_data
    )

    for line in iterable_git_data_collect:
        line = line.strip()
        if line.startswith("@@@COMMIT@@@"):
            if current_block:
                raw_commit_blocks.append(current_block)
            current_block = [line]
        elif line:
            current_block.append(line)

    if current_block:
        raw_commit_blocks.append(current_block)

    logger.debug(f"Collected {len(raw_commit_blocks)} raw commit blocks.")

    # Second pass: process raw commit blocks into GitLogEntry objects
    parsed_entries: List[GitLogEntry] = []
    iterable_git_data_process = (
        tqdm(
            raw_commit_blocks,
            desc="Processing commit blocks",
            disable=not sys.stdout.isatty(),
        )
        if TQDM_AVAILABLE
        else raw_commit_blocks
    )

    for block in iterable_git_data_process:
        entry = _process_raw_commit_block(block)
        if entry:
            parsed_entries.append(entry)

    logger.debug(f"Parsed {len(parsed_entries)} GitLogEntry objects.")
    return parsed_entries
