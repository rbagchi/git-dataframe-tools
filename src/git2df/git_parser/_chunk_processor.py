import logging
from typing import Optional, List

from ._commit_metadata_parser import GitLogEntry, _parse_commit_metadata_line
from ._file_stat_parser import FileChange

logger = logging.getLogger(__name__)


def _process_commit_chunk(chunk: str) -> Optional[GitLogEntry]:
    """Processes a single commit chunk string and fetches detailed file changes using GitCliBackend."""
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
            parts = line.strip().split("\t")
            if len(parts) == 4:
                try:
                    additions = 0 if parts[0] == "-" else int(parts[0])
                    deletions = 0 if parts[1] == "-" else int(parts[1])
                    change_type = parts[2]
                    file_path = parts[3]
                    combined_file_changes.append(
                        FileChange(
                            file_path=file_path,
                            additions=additions,
                            deletions=deletions,
                            change_type=change_type,
                        )
                    )
                except ValueError:
                    logger.warning(f"Could not parse file change line: '{line}'")
            else:
                logger.warning(f"Unexpected file change line format: '{line}'")

    return GitLogEntry(
        commit_hash=commit_metadata_dict["commit_hash"],
        parent_hash=commit_metadata_dict["parent_hash"],
        author_name=commit_metadata_dict["author_name"],
        author_email=commit_metadata_dict["author_email"],
        commit_date=commit_metadata_dict["commit_date"],
        commit_timestamp=commit_metadata_dict["commit_timestamp"],
        commit_message=commit_metadata_dict["commit_message"],
        file_changes=combined_file_changes,
    )
