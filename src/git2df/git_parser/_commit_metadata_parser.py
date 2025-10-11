import logging
import re
from datetime import datetime
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field

from ._file_stat_parser import FileChange  # Import FileChange here

logger = logging.getLogger(__name__)


@dataclass
class GitLogEntry:
    commit_hash: str
    parent_hash: Optional[str]
    author_name: str
    author_email: str
    commit_date: datetime
    commit_timestamp: int
    commit_message: str
    file_changes: List[FileChange] = field(default_factory=list)  # Use FileChange here


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
        r"---MSG_START---(?P<commit_message>.*?)---MSG_END---",
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
