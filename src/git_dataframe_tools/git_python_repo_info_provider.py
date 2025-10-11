import git
import logging
from typing import Tuple, Optional

from .git_repo_info_provider import GitRepoInfoProvider

logger = logging.getLogger(__name__)


class GitPythonRepoInfoProvider(GitRepoInfoProvider):
    """Implementation of GitRepoInfoProvider using GitPython."""

    def get_current_user_info(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        """Retrieves the current Git user's name and email for a given repository path."""
        try:
            repo = git.Repo(path)
            reader = repo.config_reader()
            name: str = str(reader.get_value("user", "name")) or "Unknown"
            email: str = str(reader.get_value("user", "email")) or "unknown@example.com"
            return name, email
        except Exception as e:
            logger.warning(f"Could not retrieve git user info using GitPython: {e}")
            return None, None

    def is_git_repo(self, path: str) -> bool:
        """Checks if the given path is a valid Git repository."""
        try:
            _ = git.Repo(path)
            return True
        except git.InvalidGitRepositoryError:
            return False
