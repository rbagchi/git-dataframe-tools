import logging
import sys
from typing import Optional, List
from tqdm import tqdm

from ._commit_metadata_parser import GitLogEntry, _parse_commit_metadata_line
from ._file_stat_parser import _parse_file_stat_line

logger = logging.getLogger(__name__)

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


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
