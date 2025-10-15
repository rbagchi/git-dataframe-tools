import abc
from typing import List, Optional

# Assuming GitLogEntry is defined in git2df.git_parser
from git2df.git_parser import GitLogEntry

class GitBackend(abc.ABC):
    """
    Abstract Base Class defining the interface for all Git backends.
    All concrete Git backends must inherit from this class and implement
    the abstract methods.
    """

    @abc.abstractmethod
    def get_log_entries(
        self,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> List[GitLogEntry]:
        """
        Retrieves a list of GitLogEntry objects based on the specified filters.

        Args:
            log_args: Optional list of arguments to pass directly to the underlying git log command.
            since: Optional string for --since argument (e.g., "1.month ago").
            until: Optional string for --until argument (e.g., "yesterday").
            author: Optional string to filter by author (e.g., "John Doe").
            grep: Optional string to filter by commit message (e.g., "fix").
            merged_only: If True, only include merged commits.
            include_paths: Optional list of paths to include.
            exclude_paths: Optional list of paths to exclude.

        Returns:
            A list of GitLogEntry objects.
        """
        pass
