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
    # Expected format: @@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---
    if len(parts) < 6:
        logger.warning(f"Malformed commit metadata line (too few parts): '{line}'")
        return None

    commit_hash_with_marker = parts[0]
    commit_hash = commit_hash_with_marker.replace("@@@COMMIT@@@", "")

    parent_hash = parts[1] if parts[1] else None
    author_name = parts[2]
    author_email = parts[3]

    date_timestamp_str = parts[4]
    raw_commit_message_part = parts[5]

    # Use regex to robustly extract commit message from raw_commit_message_part
    msg_match = re.match(
        r"---MSG_START---(?P<commit_message>.*?)---MSG_END---$",
        raw_commit_message_part,
        re.DOTALL,
    )
    if msg_match:
        commit_message = msg_match.group("commit_message")
    else:
        logger.warning(
            f"Could not find commit message delimiters in: '{raw_commit_message_part}'"
        )
        commit_message = (
            raw_commit_message_part  # Fallback to raw part if delimiters not found
        )

    try:
        commit_date_str, commit_timestamp_str = date_timestamp_str.split("\t")
        logger.debug(f"date_timestamp_str: '{date_timestamp_str}'")
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
        "commit_message": commit_message.strip(),
    }


def _parse_file_stat_line(line: str) -> Optional[FileChange]:
    """Parses a single file statistics line and returns a FileChange object."""
    parts = line.split("\t")  # Split by tab

    if len(parts) < 3:
        logger.warning(
            f"Line has too few tab-separated parts for file stat pattern: '{line}'"
        )
        return None

    added_str = parts[0]
    deleted_str = parts[1]

    change_type: str
    file_path: str

    if len(parts) == 3:
        # Format: additions deletions file_path
        # If the third part is a single char ADMT, it's likely a malformed line
        # where a change_type was intended but no file_path followed.
        if len(parts[2]) == 1 and parts[2] in "ADMT":
            logger.warning(
                f"Malformed file stat line: '{line}' - change type found but no file path."
            )
            return None
        change_type = "M"  # Default to Modified
        file_path = parts[2]
    elif len(parts) >= 4:
        # Format: additions deletions change_type file_path (or more for renames/copies)
        # For now, assume the 3rd part is change_type and the rest is file_path
        if len(parts[2]) == 1 and parts[2] in "ADMT":  # Heuristic for change type
            change_type = parts[2]
            file_path = "\t".join(parts[3:])
        else:
            # If 3rd part is not a change type, assume it's part of file_path
            # and change_type is M (e.g., "10\t5\tfile with spaces.txt")
            change_type = "M"
            file_path = "\t".join(parts[2:])
    else:
        logger.warning(f"Unexpected number of tab-separated parts: '{line}'")
        return None

    try:
        additions = 0 if added_str == "-" else int(added_str)
        deletions = 0 if deleted_str == "-" else int(deleted_str)
    except ValueError:
        logger.warning(f"Could not parse additions/deletions in line: '{line}'")
        return None

    # Ensure file_path is not empty after stripping
    if not file_path.strip():
        logger.warning(f"File path is empty in line: '{line}'")
        return None

    return FileChange(
        file_path=file_path.strip(),
        additions=additions,
        deletions=deletions,
        change_type=change_type.strip(),
    )


def _process_commit_chunk(chunk: str) -> Optional[GitLogEntry]:
    """Processes a single commit chunk string."""
    msg_end_marker = "---MSG_END---"
    end_of_msg_index = chunk.find(msg_end_marker)

    if end_of_msg_index == -1:
        logger.warning("Could not find end of message marker in chunk.")
        return None

    metadata_and_msg = chunk[: end_of_msg_index + len(msg_end_marker)]

    commit_metadata_dict = _parse_commit_metadata_line(
        "@@@COMMIT@@@" + metadata_and_msg
    )

    if not commit_metadata_dict:
        return None

    file_stats_str = chunk[end_of_msg_index + len(msg_end_marker) :]
    file_changes = []
    for line in file_stats_str.strip().split("\n"):
        if line.strip():
            file_change = _parse_file_stat_line(line.strip())
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


def parse_git_log(git_data: str) -> List[GitLogEntry]:
    """Parses raw git log string into GitLogEntry objects."""
    if not git_data.strip():
        return []

    commit_chunks = git_data.split("@@@COMMIT@@@")
    commit_chunks = [chunk for chunk in commit_chunks if chunk.strip()]

    parsed_entries: List[GitLogEntry] = []

    iterable_chunks = (
        tqdm(
            commit_chunks,
            desc="Processing commit chunks",
            disable=not sys.stdout.isatty(),
        )
        if TQDM_AVAILABLE
        else commit_chunks
    )

    for chunk in iterable_chunks:
        entry = _process_commit_chunk(chunk)
        if entry:
            parsed_entries.append(entry)

    logger.debug(f"Parsed {len(parsed_entries)} GitLogEntry objects.")
    return parsed_entries
