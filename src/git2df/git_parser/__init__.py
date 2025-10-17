import logging

from typing import List

# Import from sub-modules
from ._commit_metadata_parser import GitLogEntry
from ._file_stat_parser import FileChange
from ._chunk_processor import _process_commit_chunk

# Re-export for external usage
__all__ = ["GitLogEntry", "FileChange"]

logger = logging.getLogger(__name__)
