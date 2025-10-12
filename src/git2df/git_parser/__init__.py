import logging
import sys

from typing import List

# Conditional import for tqdm
try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Import from sub-modules
from ._commit_metadata_parser import GitLogEntry
from ._file_stat_parser import FileChange
from ._chunk_processor import _process_commit_chunk

# Re-export for external usage
__all__ = ["parse_git_log", "GitLogEntry", "FileChange"]

logger = logging.getLogger(__name__)


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
