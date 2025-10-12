import subprocess
import git
import logging
from typing import List, Optional

from git_dataframe_tools.git_repo_info_provider import GitRepoInfoProvider

logger = logging.getLogger(__name__)


class GitCliBackend:
    """A backend for git2df that interacts with the Git CLI."""

    def __init__(
        self,
        repo_path: str = ".",
        repo_info_provider: Optional[GitRepoInfoProvider] = None,
    ):
        self.repo_path = repo_path
        self.repo_info_provider = repo_info_provider
        logger.info(f"Using GitPython backend for git operations on {self.repo_path}.")

    def _get_default_branch(self) -> str:
        """Determines the default branch (main or master) for a given repository."""
        logger.debug(f"Checking for default branch in {self.repo_path}")
        try:
            repo = git.Repo(self.repo_path)
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
            logger.error(f"{self.repo_path} is not a valid git repository.")
            return "main"  # fallback for now
        return "main"

    def _build_git_log_arguments(
        self,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> List[str]:
        cmd = ["git", "log"]
        # Removed --pretty=format and --date=iso-strict from here.
        # These will be added by the caller (get_raw_log_output) for the metadata command.

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
            default_branch = self._get_default_branch()
            cmd.append("--merges")
            cmd.append(f"origin/{default_branch}")  # Assuming origin is the remote name

        if log_args:
            cmd.extend(log_args)

        # Path filters will be handled by the caller (get_raw_log_output)
        return cmd

    def _run_git_command(self, cmd: List[str]) -> str:
        logger.debug(f"Executing git command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )
            logger.debug(f"Git command stdout: {result.stdout!r}")
            logger.debug(f"Git command stderr: {result.stderr!r}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed with error: {e.stderr}")
            raise

    def _parse_numstat_output(self, numstat_output: str) -> dict[str, dict[str, str]]:
        numstat_changes: dict[str, dict[str, str]] = {}
        for line in numstat_output.strip().splitlines():
            if line.strip():
                parts = line.split("\t")
                if len(parts) == 3:  # additions\tdeletions\tfile_path
                    additions = parts[0]
                    deletions = parts[1]
                    file_path = parts[2].strip()
                    numstat_changes[file_path] = {
                        "additions": additions,
                        "deletions": deletions,
                    }
                elif len(parts) == 4:  # Rename/Copy format: A\tB\told\tnew
                    additions = parts[0]
                    deletions = parts[1]
                    file_path = parts[3].strip()  # Use new path as key
                    numstat_changes[file_path] = {
                        "additions": additions,
                        "deletions": deletions,
                    }
                else:
                    logger.warning(f"Unexpected numstat line format: '{line}'")
        return numstat_changes

    def _parse_name_status_output(self, name_status_output: str) -> dict[str, dict[str, str]]:
        name_status_changes: dict[str, dict[str, str]] = {}
        for line in name_status_output.strip().splitlines():
            if line.strip():
                parts = line.split("\t")
                if len(parts) == 2:  # change_type\tfile_path
                    change_type = parts[0]
                    file_path = parts[1].strip()
                    if file_path in name_status_changes:
                        name_status_changes[file_path]["change_type"] = change_type
                    else:
                        name_status_changes[file_path] = {
                            "change_type": change_type
                        }
                elif len(parts) == 3:  # Rename/Copy format: RXXX\told\tnew
                    change_type = parts[0]
                    file_path = parts[2].strip()  # Use new path as key
                    if file_path in name_status_changes:
                        name_status_changes[file_path]["change_type"] = change_type
                    else:
                        name_status_changes[file_path] = {
                            "change_type": change_type
                        }
                else:
                    logger.warning(f"Unexpected name-status line format: '{line}'")
        return name_status_changes

    def get_raw_log_output(
        self,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> str:
        # Build base arguments without pretty format or path filters
        base_args_no_pretty_no_paths = self._build_git_log_arguments(
            log_args,
            since,
            until,
            author,
            grep,
            merged_only,
            None,  # include_paths handled separately
            None,  # exclude_paths handled separately
        )

        # Construct path filters
        path_filters = []
        if include_paths:
            path_filters.append("--")
            path_filters.extend(include_paths)
        if exclude_paths:
            if not path_filters:  # Add -- only if not already added by include_paths
                path_filters.append("--")
            for p in exclude_paths:
                path_filters.append(f":(exclude){p}")

        # 1. Get commit hashes that match the filters
        rev_list_cmd = (
            ["git", "rev-list", "--all"]
            + base_args_no_pretty_no_paths[2:]
            + path_filters
        )
        commit_hashes_output = self._run_git_command(rev_list_cmd)
        commit_hashes = [
            h.strip() for h in commit_hashes_output.strip().splitlines() if h.strip()
        ]

        if not commit_hashes:
            return ""

        combined_output_lines = []

        for commit_hash in commit_hashes:
            # Get metadata for the current commit
            metadata_cmd = (
                ["git", "show", commit_hash]
                + [
                    "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---",
                    "--date=iso-strict",
                ]
                + path_filters
            )
            metadata_output = self._run_git_command(metadata_cmd)

            # Get numstat for the current commit
            numstat_cmd = ["git", "show", commit_hash, "--numstat"] + path_filters
            numstat_output = self._run_git_command(numstat_cmd)

            # Get name-status for the current commit
            name_status_cmd = [
                "git",
                "show",
                commit_hash,
                "--name-status",
            ] + path_filters
            name_status_output = self._run_git_command(name_status_cmd)

            # Combine outputs for this commit
            combined_output_lines.append(
                metadata_output.strip()
            )  # metadata_output already has @@@COMMIT@@@ and ends with \n

            numstat_changes = self._parse_numstat_output(numstat_output)
            name_status_changes = self._parse_name_status_output(name_status_output)

            # Combine and format file changes
            all_file_paths = set(numstat_changes.keys()).union(
                name_status_changes.keys()
            )
            for file_path in all_file_paths:
                additions = numstat_changes.get(file_path, {}).get("additions", "0")
                deletions = numstat_changes.get(file_path, {}).get("deletions", "0")
                change_type = name_status_changes.get(file_path, {}).get(
                    "change_type", "U"
                )
                combined_output_lines.append(
                    f"{additions}\t{deletions}\t{change_type}\t{file_path}"
                )

        return "\n".join(combined_output_lines)
