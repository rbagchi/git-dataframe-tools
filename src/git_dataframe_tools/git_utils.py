import git
import logging
import os

logger = logging.getLogger(__name__)

def check_git_repo(repo_path: str) -> bool:
    """Checks if the given path is a valid Git repository."""
    try:
        _ = git.Repo(repo_path)
        return True
    except git.InvalidGitRepositoryError:
        return False

def get_current_git_user(repo_path: str) -> tuple[str, str]:
    """Retrieves the current Git user name and email from the repository config."""
    repo = git.Repo(repo_path)
    reader = repo.config_reader()
    try:
        name = reader.get_value("user", "name")
        email = reader.get_value("user", "email")
        return name, email
    except Exception as e:
        logger.warning(f"Could not retrieve git user info: {e}")
        return "Unknown", "unknown@example.com"
