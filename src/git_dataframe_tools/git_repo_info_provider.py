from typing import Protocol, Tuple, Optional


class GitRepoInfoProvider(Protocol):
    """Interface for providing Git repository information."""

    def get_current_user_info(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        """Returns the current Git user's name and email for a given repository path."""
        ...

    def is_git_repo(self, path: str) -> bool:
        """Checks if the given path is a valid Git repository."""
        ...
