import logging
from datetime import datetime
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field

from ._file_stat_parser import FileChange  # Import FileChange here

logger = logging.getLogger(__name__)


@dataclass
class GitLogEntry:
    commit_hash: str
    author_name: str
    author_email: str
    commit_date: datetime
    commit_timestamp: int
    commit_message: str
    parent_hashes: List[str] = field(default_factory=list)
    file_changes: List[FileChange] = field(default_factory=list)  # Use FileChange here

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commit_hash": self.commit_hash,
            "parent_hashes": self.parent_hashes,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "commit_date": self.commit_date,
            "commit_timestamp": self.commit_timestamp,
            "commit_message": self.commit_message,
            "file_changes": [fc.to_dict() for fc in self.file_changes], # Assuming FileChange also has to_dict()
        }


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

    parent_hashes = parts[1].split() if parts[1] else []
    author_name = parts[2]
    author_email = parts[3]

    date_timestamp_str = parts[4]
    raw_commit_message_part = parts[5]

    # Use string partitioning to extract commit message
    before, sep, after = raw_commit_message_part.partition("---MSG_START---")
    if sep:
        commit_message, sep, after = after.partition("---MSG_END---")
    else:
        commit_message = (
            raw_commit_message_part  # Fallback if start delimiter not found
        )

    if not commit_message:
        logger.warning(
            f"Could not find commit message delimiters in: '{raw_commit_message_part}'"
        )
        commit_message = (
            raw_commit_message_part  # Fallback to raw part if delimiters not found
        )

    try:
        commit_date_str, commit_timestamp_str = date_timestamp_str.split("\t")
        logger.debug(f"date_timestamp_str: '{date_timestamp_str}'")
        # Replace 'Z' with '+00:00' for consistent ISO format parsing
        commit_date_str = commit_date_str.replace("Z", "+00:00")
        commit_date = datetime.fromisoformat(commit_date_str)
        commit_timestamp = int(commit_timestamp_str)
    except ValueError:
        logger.warning(
            f"Could not parse commit date or timestamp: '{date_timestamp_str}' in line '{line}'"
        )
        return None

    return {
        "commit_hash": commit_hash,
        "parent_hashes": parent_hashes,
        "author_name": author_name,
        "author_email": author_email,
        "commit_date": commit_date,
        "commit_timestamp": commit_timestamp,
        "commit_message": commit_message.strip(),
    }
