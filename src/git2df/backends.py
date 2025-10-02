from typing import List, Optional
from git2df.git_cli_utils import _run_git_command
import subprocess

class GitCliBackend:
    """A backend for git2df that interacts with the Git CLI."""

    def _get_default_branch(self, repo_path: str) -> str:
        """Determines the default branch (main or master) for a given repository."""
        try:
            subprocess.run(['git', 'show-ref', '--verify', 'refs/heads/main'], check=True, capture_output=True, cwd=repo_path)
            return 'main'
        except subprocess.CalledProcessError:
            try:
                subprocess.run(['git', 'show-ref', '--verify', 'refs/heads/master'], check=True, capture_output=True, cwd=repo_path)
                return 'master'
            except subprocess.CalledProcessError:
                return 'main' # Default to main even if not found, git will handle the error if it doesn't exist

    def get_raw_log_output(self, repo_path: str, log_args: Optional[List[str]] = None,
                           since: Optional[str] = None, until: Optional[str] = None,
                           author: Optional[str] = None, grep: Optional[str] = None,
                           merged_only: bool = False, include_paths: Optional[List[str]] = None,
                           exclude_paths: Optional[List[str]] = None) -> str:
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

        cmd = ["log"] + log_args
        if since:
            cmd.append(f"--since={since}")
        if until:
            cmd.append(f"--until={until}")
        if author:
            cmd.append(f"--author={author}")
        if grep:
            cmd.append(f"--grep={grep}")
        if merged_only:
            default_branch = self._get_default_branch(repo_path)
            cmd.extend(['--merges', f'origin/{default_branch}'])
        
        if include_paths:
            cmd.extend(['--'] + include_paths)
        if exclude_paths:
            for p in exclude_paths:
                cmd.extend([f':(exclude){p}'])

        raw_log_output = _run_git_command(cmd, cwd=repo_path)
        return raw_log_output
