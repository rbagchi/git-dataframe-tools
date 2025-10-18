import subprocess
import logging
from typing import List, Optional

from git_dataframe_tools.git_repo_info_provider import GitRepoInfoProvider
from git2df.backend_interface import GitBackend
from git2df.git_parser import GitLogEntry
from git2df.git_parser._chunk_processor import _process_commit_chunk

logger = logging.getLogger(__name__)


def _parse_name_status_line(line: str, name_status_changes: dict[str, dict[str, str]]):
    if not line.strip():
        return
    parts = line.split("\t")
    if len(parts) == 2:
        change_type = parts[0]
        file_path = parts[1].strip()
        if file_path in name_status_changes:
            name_status_changes[file_path]["change_type"] = change_type
        else:
            name_status_changes[file_path] = {
                "change_type": change_type
            }
    elif len(parts) == 3:
        change_type = parts[0]
        file_path = parts[2].strip()
        if file_path in name_status_changes:
            name_status_changes[file_path]["change_type"] = change_type
        else:
            name_status_changes[file_path] = {
                "change_type": change_type
            }
    else:
        logger.warning(f"Unexpected name-status line format: '{line}'")

class GitCliBackend(GitBackend):
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
        """
        Returns the default branch of the remote 'origin'.
        """
        try:
            result = self._run_git_command(["git", "remote", "show", "origin"])
            for line in result.splitlines():
                if "HEAD branch" in line:
                    return line.split(":")[-1].strip()
            return "main" # Fallback to main if not found
        except subprocess.CalledProcessError as e:
            logger.warning(
                "Could not determine default branch from remote 'origin'. "
                "Falling back to 'main'. Error: %s", e.stderr
            )
            return "main"

    def _parse_git_data_to_log_entries(self, git_data: str) -> List[GitLogEntry]:
        if not git_data.strip():
            return []

        commit_chunks = git_data.split("@@@COMMIT@@@")
        commit_chunks = [chunk for chunk in commit_chunks if chunk.strip()]

        parsed_entries: List[GitLogEntry] = []

        for chunk in commit_chunks:
            entry = _process_commit_chunk(chunk)
            if entry:
                parsed_entries.append(entry)

        logger.debug(f"Parsed {len(parsed_entries)} GitLogEntry objects.")
        return parsed_entries

    def _get_commit_hashes(self, base_args_no_pretty_no_paths: List[str], path_filters: List[str]) -> List[str]:
        rev_list_cmd = (
            ["git", "rev-list", "--all"]
            + base_args_no_pretty_no_paths[2:]
            + path_filters
        )
        commit_hashes_output = self._run_git_command(rev_list_cmd)
        commit_hashes = [
            h.strip() for h in commit_hashes_output.strip().splitlines() if h.strip()
        ]
        return commit_hashes

    def _build_path_filters(self, include_paths: Optional[List[str]], exclude_paths: Optional[List[str]]) -> List[str]:
        path_filters = []
        if include_paths:
            path_filters.append("--")
            path_filters.extend(include_paths)
        if exclude_paths:
            if not path_filters:
                path_filters.append("--")
            for p in exclude_paths:
                path_filters.append(f":(exclude){p}")
        return path_filters

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
        Retrieves a list of GitLogEntry objects by calling get_raw_log_output
        and then parsing the result.
        """
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

        path_filters = self._build_path_filters(include_paths, exclude_paths)

        commit_hashes = self._get_commit_hashes(base_args_no_pretty_no_paths, path_filters)

        if not commit_hashes:
            return []

        combined_output_lines = []

        for commit_hash in commit_hashes:
            combined_output_lines.extend(self._process_commit(commit_hash, path_filters))

        git_data = "\n".join(combined_output_lines)

        return self._parse_git_data_to_log_entries(git_data)


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

        arg_map = {
            "--since": since,
            "--until": until,
            "--grep": grep,
        }
        for arg, value in arg_map.items():
            if value:
                cmd.extend([arg, value])

        if author:
            author_parts = [p.strip() for p in author.split("|") if p.strip()]
            for part in author_parts:
                cmd.extend(["--author", part])

        if merged_only:
            try:
                # Check if 'origin' remote exists
                self._run_git_command(["git", "remote", "show", "origin"])
                default_branch = self._get_default_branch()
                cmd.extend(["--merges", f"origin/{default_branch}"])
            except subprocess.CalledProcessError:
                # If 'origin' remote does not exist, just use --merges
                cmd.append("--merges")

        if log_args:
            cmd.extend(log_args)

        pathspecs = []
        if include_paths:
            pathspecs.extend(include_paths)
        if exclude_paths:
            pathspecs.extend([f":(exclude){p}" for p in exclude_paths])

        if pathspecs:
            cmd.append("--")
            cmd.extend(pathspecs)
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
        lines = numstat_output.strip().splitlines()
        if lines and len(lines[0]) == 40 and all(c in '0123456789abcdef' for c in lines[0].lower()):
            lines = lines[1:]

        for line in lines:
            if line.strip():
                parts = line.split("\t")
                if len(parts) == 3:
                    additions = parts[0]
                    deletions = parts[1]
                    file_path = parts[2].strip()
                    numstat_changes[file_path] = {
                        "additions": additions,
                        "deletions": deletions,
                    }
                elif len(parts) == 4:
                    additions = parts[0]
                    deletions = parts[1]
                    file_path = parts[3].strip()
                    numstat_changes[file_path] = {
                        "additions": additions,
                        "deletions": deletions,
                    }
                else:
                    logger.warning(f"Unexpected numstat line format: '{line}'")
        return numstat_changes

    def _parse_name_status_output(self, name_status_output: str) -> dict[str, dict[str, str]]:
        name_status_changes: dict[str, dict[str, str]] = {}
        lines = name_status_output.strip().splitlines()
        if lines and len(lines[0]) == 40 and all(c in '0123456789abcdef' for c in lines[0].lower()):
            lines = lines[1:]

        for line in lines:
            _parse_name_status_line(line, name_status_changes)
        return name_status_changes

    def _process_commit(self, commit_hash: str, path_filters: List[str]) -> List[str]:
        metadata_cmd = (
            ["git", "show", commit_hash, "--no-patch"]
            + [
                "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%s---MSG_END---",
                "--date=iso-strict",
            ]
            + path_filters
        )
        metadata_output = self._run_git_command(metadata_cmd)

        parent_hashes = metadata_output.split("@@@FIELD@@@")[1].strip()

        if not parent_hashes:
            numstat_cmd = ["git", "diff-tree", "-r", "--numstat", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", commit_hash] + path_filters
            name_status_cmd = ["git", "diff-tree", "-r", "--name-status", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", commit_hash] + path_filters
        else:
            numstat_cmd = ["git", "diff-tree", "-r", "--numstat", commit_hash] + path_filters
            name_status_cmd = (
                ["git", "diff-tree", "-r", "--name-status", commit_hash]
                + path_filters
            )

        numstat_output = self._run_git_command(numstat_cmd)
        name_status_output = self._run_git_command(name_status_cmd)

        commit_lines = [metadata_output.strip()]

        numstat_changes = self._parse_numstat_output(numstat_output)
        name_status_changes = self._parse_name_status_output(name_status_output)

        all_file_paths = set(numstat_changes.keys()).union(
            name_status_changes.keys()
        )
        for file_path in all_file_paths:
            additions = numstat_changes.get(file_path, {}).get("additions", "0")
            deletions = numstat_changes.get(file_path, {}).get("deletions", "0")
            change_type = name_status_changes.get(file_path, {}).get(
                "change_type", "U"
            )
            commit_lines.append(
                f"{additions}\t{deletions}\t{change_type}\t{file_path}"
            )
        return commit_lines
