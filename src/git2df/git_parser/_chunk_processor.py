import logging
from typing import Optional, List

from ._commit_metadata_parser import GitLogEntry, _parse_commit_metadata_line
from ._file_stat_parser import FileChange

logger = logging.getLogger(__name__)


def _process_commit_chunk(chunk: str) -> Optional[GitLogEntry]:
    logger.debug(f"Processing chunk: {chunk[:100]}...") # Print first 100 chars of chunk
    """Processes a single commit chunk string and extracts commit metadata and file changes."""
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

    file_changes_raw = chunk[end_of_msg_index + len(msg_end_marker) :].strip()

    combined_file_changes: List[FileChange] = []

    for line in file_changes_raw.split("\n"):
        if line.strip():
            file_change = _parse_single_file_change_line(line)
            if file_change:
                combined_file_changes.append(file_change)

    return GitLogEntry(
        commit_hash=commit_metadata_dict["commit_hash"],
        parent_hashes=commit_metadata_dict["parent_hashes"],
        author_name=commit_metadata_dict["author_name"],
        author_email=commit_metadata_dict["author_email"],
        commit_date=commit_metadata_dict["commit_date"],
        commit_timestamp=commit_metadata_dict["commit_timestamp"],
        commit_message=commit_metadata_dict["commit_message"],
        file_changes=combined_file_changes,
    )

def _is_ignorable_line(line: str) -> bool:
    """Checks if a line from git diff output should be ignored."""
    if not line:
        return True

    prefixes = ("diff --git", "old mode", "new mode", "index", "--- a/", "+++ b/", "@@ - ")
    if line.startswith(prefixes):
        return True

    if len(line) == 40 and all(c in "0123456789abcdefABCDEF" for c in line):
        return True

    return False

def _parse_4_part_line(parts: List[str]) -> Optional[FileChange]:
    try:
        additions = 0 if parts[0] == "-" else int(parts[0])
        deletions = 0 if parts[1] == "-" else int(parts[1])
        change_type = parts[2]
        file_path = parts[3]
        return FileChange(
            file_path=file_path,
            additions=additions,
            deletions=deletions,
            change_type=change_type,
        )
    except ValueError:
        return None

def _parse_3_part_line(parts: List[str]) -> Optional[FileChange]:
    try:
        additions = 0 if parts[0] == "-" else int(parts[0])
        deletions = 0 if parts[1] == "-" else int(parts[1])
        file_path = parts[2]
        return FileChange(
            file_path=file_path,
            additions=additions,
            deletions=deletions,
            change_type="",  # No change type provided in 3-part format
        )
    except ValueError:
        return None

def _parse_single_file_change_line(line: str) -> Optional[FileChange]:
    """Parses a single line representing a file change and returns a FileChange object."""
    line = line.strip()
    if _is_ignorable_line(line):
        return None

    parts = line.strip().split("\t")
    file_change = None
    if len(parts) == 4:
        file_change = _parse_4_part_line(parts)
        if not file_change:
            logger.warning(f"Could not parse 4-part file change line: '{line}'")
    elif len(parts) == 3:
        file_change = _parse_3_part_line(parts)
        if not file_change:
            logger.warning(f"Could not parse 3-part file change line: '{line}'")
    else:
        logger.warning(f"Unexpected file change line format: '{line}'")
    
    return file_change
