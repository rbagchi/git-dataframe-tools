import logging
from typing import List, Optional
from git2df.git_cli_utils import _run_git_command
import subprocess

logger = logging.getLogger(__name__)


class GitCliBackend:
    """A backend for git2df that interacts with the Git CLI."""

    def _get_default_branch(self, repo_path: str) -> str:
        """Determines the default branch (main or master) for a given repository."""
        logger.debug(f"Checking for default branch in {repo_path}")
        try:
            logger.debug("Attempting to find 'main' branch.")
            subprocess.run(
                ["git", "show-ref", "--verify", "refs/heads/main"],
                check=True,
                capture_output=True,
                cwd=repo_path,
            )
            logger.info("Found 'main' as default branch.")
            return "main"
        except subprocess.CalledProcessError:
            logger.debug("Main branch not found, attempting to find 'master' branch.")
            try:
                subprocess.run(
                    ["git", "show-ref", "--verify", "refs/heads/master"],
                    check=True,
                    capture_output=True,
                    cwd=repo_path,
                )
                logger.info("Found 'master' as default branch.")
                return "master"
            except subprocess.CalledProcessError:
                logger.warning(
                    "Neither 'main' nor 'master' found as default branch. Defaulting to 'main'."
                )
                return "main"  # Default to main even if not found, git will handle the error if it doesn't exist

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
        if log_args is None:
            log_args = []
        full_cmd = ["git"] + ["log"] + log_args
        if since:
            full_cmd.append(f"--since={since}")
        if until:
            full_cmd.append(f"--until={until}")
        if author:
            full_cmd.append(f"--author={author}")
        if grep:
            full_cmd.append(f"--grep={grep}")
        if merged_only:
            default_branch = self._get_default_branch(repo_path)
            full_cmd.extend(["--merges", f"origin/{default_branch}"])

        if include_paths:
            full_cmd.extend(["--"] + include_paths)
        if exclude_paths:
            for p in exclude_paths:
                full_cmd.extend([f":(exclude){p}"])

        logger.debug(f"Executing git command: {' '.join(full_cmd)} in {repo_path}")
        raw_log_output = _run_git_command(
            full_cmd[1:], cwd=repo_path
        )  # _run_git_command expects command without 'git'
        logger.debug(f"Raw git log output (first 200 chars): {raw_log_output[:200]}...")
        return raw_log_output
