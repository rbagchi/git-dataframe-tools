import subprocess
import git
import logging
from typing import List, Optional, Any

logger = logging.getLogger(__name__)


class GitCliBackend:
    """A backend for git2df that interacts with the Git CLI."""

    def __init__(self):
        logger.info("Using GitPython backend for git operations.")

    def _get_default_branch(self, repo_path: str) -> str:
        """Determines the default branch (main or master) for a given repository."""
        logger.debug(f"Checking for default branch in {repo_path}")
        try:
            repo = git.Repo(repo_path)
            if "main" in repo.heads:
                logger.info("Found 'main' as default branch.")
                return "main"
            elif "master" in repo.heads:
                logger.info("Found 'master' as default branch.")
                return "master"
            else:
                logger.warning(
                    "Neither 'main' nor 'master' found as default branch. Defaulting to 'main'."
                )
                return "main"
        except git.InvalidGitRepositoryError:
            logger.error(f"{repo_path} is not a valid git repository.")
            return "main"  # fallback for now
        return "main"

    def get_raw_log_output(
        self,
        repo_path: str,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Executes a git log command and returns its raw string output.

        Args:
            repo_path: The path to the git repository.
            log_args: Optional list of arguments to pass to 'git log'.
            since: Optional string for --since argument (e.g., "1.month ago").
            until: Optional string for --until argument (e.g., "yesterday").
            author: Optional string to filter by author (e.g., "John Doe").
            grep: Optional string to filter by commit message (e.g., "fix").
            merged_only: If True, only include merged commits.
            include_paths: Optional list of paths to include.
            exclude_paths: Optional list of paths to exclude.

        Returns:
            The raw stdout from the 'git log' command.
        """
        cmd = ["git", "log"]

        # Always include --numstat for file changes and the custom pretty format
        cmd.append("--numstat")
        cmd.append(
            "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad@@@FIELD@@@%s"
        )
        cmd.append("--date=iso") # Ensure ISO format for consistent date parsing

        if since:
            cmd.extend(["--since", since])
        if until:
            cmd.extend(["--until", until])
        if author:
            cmd.extend(["--author", author])
        if grep:
            cmd.extend(["--grep", grep])
        if merged_only:
            # For merged_only, we need to find the default branch first
            # This still uses GitPython for _get_default_branch, but the log itself is CLI
            default_branch = self._get_default_branch(repo_path)
            cmd.append("--merges")
            cmd.append(f"origin/{default_branch}") # Assuming origin is the remote name

        if log_args:
            cmd.extend(log_args)

        if include_paths:
            cmd.append("--") # Separator for paths
            cmd.extend(include_paths)
        if exclude_paths:
            cmd.append("--") # Separator for paths
            for p in exclude_paths:
                cmd.append(f":(exclude){p}")

        logger.debug(f"Executing git log command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed with error: {e.stderr}")
            raise
