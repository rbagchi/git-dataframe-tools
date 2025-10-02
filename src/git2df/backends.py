from typing import List
from git2df.git_cli_utils import _run_git_command

class GitCliBackend:
    """A backend for git2df that interacts with the Git CLI."""

    def get_raw_log_output(self, repo_path: str, log_args: List[str]) -> str:
        """
        Executes a git log command and returns its raw string output.
        
        Args:
            repo_path: The path to the git repository.
            log_args: A list of arguments to pass to 'git log'.
            
        Returns:
            The raw stdout from the 'git log' command.
        """
        cmd = ["log"] + log_args
        return _run_git_command(cmd, cwd=repo_path)
