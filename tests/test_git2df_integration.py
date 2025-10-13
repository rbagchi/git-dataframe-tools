import subprocess
from datetime import datetime
import re
from typing import Optional, Union


# Helper function to create a dummy git repo
def create_dummy_repo(tmp_path):
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    # Commit 1
    (repo_path / "file1.txt").write_text("line1\nline2")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

    # Commit 2 (Author One)
    subprocess.run(
        ["git", "config", "user.email", "author1@example.com"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Author One"], cwd=repo_path, check=True
    )
    (repo_path / "file2.txt").write_text("new file")
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add file2"], cwd=repo_path, check=True)

    # Commit 3 (Author Two)
    subprocess.run(
        ["git", "config", "user.email", "author2@example.com"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Author Two"], cwd=repo_path, check=True
    )
    (repo_path / "file1.txt").write_text("line1\nline2\nline3")  # 1 added
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Modify file1"], cwd=repo_path, check=True)

    # Commit 4 (Author One, another commit)
    subprocess.run(
        ["git", "config", "user.email", "author1@example.com"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Author One"], cwd=repo_path, check=True
    )
    (repo_path / "file2.txt").write_text("new file\nmore content")  # 1 added
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Modify file2 again"], cwd=repo_path, check=True
    )

    return repo_path


def _parse_commit_metadata_line_for_comparison(line: str) -> Optional[dict]:
    parts = line.split("--")
    # Expected format: --%H--%P--%an--%ae--%ad--%s
    if len(parts) >= 7:
        commit_hash = parts[1]
        parent_hash = parts[2] if parts[2] else None
        author_name = parts[3]
        author_email = parts[4]
        commit_date_str = parts[5]
        commit_message = parts[6]

        return {
            "commit_hash": commit_hash,
            "parent_hash": parent_hash,
            "author_name": author_name,
            "author_email": author_email,
            "commit_date": datetime.fromisoformat(commit_date_str),
            "commit_message": commit_message,
        }
    return None

def _parse_file_stat_line_for_comparison(line: str) -> Optional[dict]:
    stat_match = re.match(r"^(\d+|-)\t(\d+|-)\t(.+)$", line)
    if stat_match:
        added_str, deleted_str, file_path = stat_match.groups()

        additions = 0 if added_str == "-" else int(added_str)
        deletions = 0 if deleted_str == "-" else int(deleted_str)

        change_type = "M"
        if additions > 0 and deletions == 0:
            change_type = "A"
        elif additions == 0 and deletions > 0:
            change_type = "D"

        return {
            "file_paths": file_path,
            "change_type": change_type,
            "additions": additions,
            "deletions": deletions,
        }
    return None

def _finalize_commit_data(commits_data: list[dict], current_commit: dict, current_files: list[dict]):
    if current_commit and current_files:
        for file_info in current_files:
            commit_record = current_commit.copy()
            commit_record.update(file_info)
            commits_data.append(commit_record)

def _parse_raw_git_log_for_comparison(raw_log_output: str) -> list[dict]:
    """
    Parses raw git log output (with --numstat and --pretty format)
    to extract commit details and file stats per commit for comparison.
    """
    commits_data: list[dict] = []
    current_commit: dict[str, Union[str, datetime, None, int]] = {}
    current_files: list[dict[str, Union[str, int]]] = []

    for line in raw_log_output.splitlines():
        line = line.strip()

        if not line:
            _finalize_commit_data(commits_data, current_commit, current_files)
            current_commit = {}
            current_files = []
            continue

        if line.startswith("--"):
            parsed_metadata = _parse_commit_metadata_line_for_comparison(line)
            if parsed_metadata:
                _finalize_commit_data(commits_data, current_commit, current_files)
                current_commit = parsed_metadata
                current_files = []
        else:
            if current_commit:
                parsed_file_stat = _parse_file_stat_line_for_comparison(line)
                if parsed_file_stat:
                    current_files.append(parsed_file_stat)

    _finalize_commit_data(commits_data, current_commit, current_files)

    return commits_data
