import logging
from typing import Optional, Any, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    file_path: str
    additions: int
    deletions: int
    change_type: str
    old_file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "additions": self.additions,
            "deletions": self.deletions,
            "change_type": self.change_type,
            "old_file_path": self.old_file_path,
        }


def _parse_numstat_line(line: str) -> Optional[FileChange]:
    """Parses a single --numstat line and returns a FileChange object."""
    parts = line.split("\t")  # Split by tab

    if len(parts) < 3:
        logger.warning(
            f"Line has too few tab-separated parts for numstat pattern: '{line}'"
        )
        return None

    added_str = parts[0]
    deleted_str = parts[1]
    file_path = "\t".join(parts[2:])

    try:
        additions = 0 if added_str == "-" else int(added_str)
        deletions = 0 if deleted_str == "-" else int(deleted_str)
    except ValueError:
        logger.warning(f"Could not parse additions/deletions in numstat line: '{line}'")
        return None

    if not file_path.strip():
        logger.warning(f"File path is empty in numstat line: '{line}'")
        return None

    return FileChange(
        file_path=file_path.strip(),
        additions=additions,
        deletions=deletions,
        change_type="",  # Will be filled by name-status
    )


def _parse_name_status_line(line: str) -> Optional[FileChange]:
    """Parses a single --name-status line and returns a FileChange object."""
    parts = line.split("\t")  # Split by tab

    if not parts:
        logger.warning(f"Empty line for name-status pattern: '{line}'")
        return None

    change_type = parts[0]
    file_path = "\t".join(parts[1:])
    old_file_path: Optional[str] = None

    if not change_type.strip():
        logger.warning(f"Change type is empty in name-status line: '{line}'")
        return None
    if not file_path.strip():
        logger.warning(f"File path is empty in name-status line: '{line}'")
        return None

    # Handle renames/copies: R100\told_name.txt\tnew_name.txt or C100\told_name.txt\tnew_name.txt
    if (change_type.startswith("R") or change_type.startswith("C")) and len(parts) >= 3:
        old_file_path = parts[1]
        file_path = parts[2]
    else:
        file_path = "\t".join(parts[1:])

    return FileChange(
        file_path=file_path.strip(),
        additions=0,  # Will be filled by numstat
        deletions=0,  # Will be filled by numstat
        change_type=change_type.strip(),
        old_file_path=old_file_path.strip() if old_file_path else None,
    )
