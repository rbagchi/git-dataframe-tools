import subprocess
from datetime import datetime
import re
from typing import Union


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


def _parse_raw_git_log_for_comparison(raw_log_output: str) -> list[dict]:
    """
    Parses raw git log output (with --numstat and --pretty format)
    to extract commit details and file stats per commit for comparison.
    """
    commits_data = []
    current_commit: dict[str, Union[str, datetime, None, int]] = {}
    current_files: list[dict[str, Union[str, int]]] = []

    for line in raw_log_output.splitlines():
        line = line.strip()

        if not line:
            if current_commit and current_files:
                for file_info in current_files:
                    commit_record = current_commit.copy()
                    commit_record.update(file_info)
                    commits_data.append(commit_record)
            current_commit = {}
            current_files = []
            continue

        if line.startswith("--"):
            if current_commit and current_files:
                for file_info in current_files:
                    commit_record = current_commit.copy()
                    commit_record.update(file_info)
                    commits_data.append(commit_record)

            current_files = []  # Reset current_files for the new commit

            parts = line.split("--")
            # Expected format: --%H--%P--%an--%ae--%ad--%s
            if len(parts) >= 7:
                commit_hash = parts[1]
                parent_hash = parts[2] if parts[2] else None
                author_name = parts[3]
                author_email = parts[4]
                commit_date_str = parts[5]
                commit_message = parts[6]

                current_commit = {
                    "commit_hash": commit_hash,
                    "parent_hash": parent_hash,
                    "author_name": author_name,
                    "author_email": author_email,
                    "commit_date": datetime.fromisoformat(commit_date_str),
                    "commit_message": commit_message,
                }
        else:
            if current_commit:
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

                    current_files.append(
                        {
                            "file_paths": file_path,
                            "change_type": change_type,
                            "additions": additions,
                            "deletions": deletions,
                        }
                    )

    if current_commit and current_files:
        for file_info in current_files:
            commit_record = current_commit.copy()
            commit_record.update(file_info)
            commits_data.append(commit_record)

    return commits_data
