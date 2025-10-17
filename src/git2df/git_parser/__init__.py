import logging

# Import from sub-modules
from ._commit_metadata_parser import GitLogEntry
from ._file_stat_parser import FileChange

# Re-export for external usage
__all__ = ["GitLogEntry", "FileChange"]

logger = logging.getLogger(__name__)
