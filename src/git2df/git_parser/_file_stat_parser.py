import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    file_path: str
    additions: int
    deletions: int
    change_type: str


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
