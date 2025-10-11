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
    logger.debug(f"raw_commit_message_part: '{raw_commit_message_part}'")

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
    stat_match = re.match(r"^(\d+|-)\s+(\d+|-)\s+(?:([ADMT])\s+)?(.+)", line)
    if not stat_match:
        logger.warning(f"Line did not match file stat pattern: '{line}'")
        return None

    added_str, deleted_str, change_type_match, file_path = stat_match.groups()

    change_type = change_type_match if change_type_match else "M"

    additions = 0 if added_str == "-" else int(added_str)
    deletions = 0 if deleted_str == "-" else int(deleted_str)

    return FileChange(
        file_path=file_path.strip(),
        additions=additions,
        deletions=deletions,
        change_type=change_type,
    )


def _process_commit_chunk(chunk: str) -> Optional[GitLogEntry]:
    """Processes a single commit chunk string."""
    msg_end_marker = "---MSG_END---"
    end_of_msg_index = chunk.find(msg_end_marker)

    if end_of_msg_index == -1:
        logger.warning("Could not find end of message marker in chunk.")
        return None

    metadata_and_msg = chunk[:end_of_msg_index + len(msg_end_marker)]
    
    commit_metadata_dict = _parse_commit_metadata_line("@@@COMMIT@@@" + metadata_and_msg)
    
    if not commit_metadata_dict:
        return None
        
    file_stats_str = chunk[end_of_msg_index + len(msg_end_marker):]
    file_changes = []
    for line in file_stats_str.strip().split('\n'):
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