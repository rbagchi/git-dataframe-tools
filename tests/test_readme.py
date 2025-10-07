import pytest
import os
import subprocess
import re
from pathlib import Path
import shutil
from datetime import datetime, timedelta

def test_readme_commands(tmp_path: Path):
    # Create a dummy git repository in the temporary directory
    os.chdir(tmp_path)
    project_root = Path(__file__).parent.parent
    shutil.copy(project_root / "pyproject.toml", tmp_path)
    shutil.copytree(project_root / "src", tmp_path / "src")

    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    (tmp_path / "file1.txt").write_text("file1 content")
    subprocess.run(["git", "add", "file1.txt"], check=True)
    subprocess_env = os.environ.copy()
    subprocess_env["GIT_COMMITTER_DATE"] = (datetime.now() - timedelta(days=30)).isoformat()
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, env=subprocess_env)
    (tmp_path / "file1.txt").write_text("file1 content updated")
    subprocess.run(["git", "add", "file1.txt"], check=True)
    subprocess_env["GIT_COMMITTER_DATE"] = (datetime.now() - timedelta(days=15)).isoformat()
    subprocess.run(["git", "commit", "-m", "Update file1"], check=True, env=subprocess_env)
    (tmp_path / "file2.txt").write_text("file2 content")
    subprocess.run(["git", "add", "file2.txt"], check=True)
    subprocess_env["GIT_COMMITTER_DATE"] = (datetime.now() - timedelta(days=1)).isoformat()
    subprocess.run(["git", "commit", "-m", "Add file2"], check=True, env=subprocess_env)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path / "src") + os.pathsep + str(project_root)

    # 1. Install the package
    subprocess.run("uv pip install -e .", shell=True, check=True, capture_output=True, text=True, env=env)

    # 2. Run git-df to create a parquet file
    git_df_command = "python -m git_dataframe_tools.cli.git_df --repo-path . --output commits.parquet --since \"1 year ago\" --until \"now\""
    subprocess.run(git_df_command, shell=True, check=True, capture_output=True, text=True, env=env)

    # 3. Run git-scoreboard with the created parquet file
    git_scoreboard_command = "python -m git_dataframe_tools.cli.scoreboard --df-path commits.parquet --since \"1 year ago\" --until \"now\""
    subprocess.run(git_scoreboard_command, shell=True, check=True, capture_output=True, text=True, env=env)

    # 4. Run git-scoreboard directly on the git repo
    git_scoreboard_direct_command = "python -m git_dataframe_tools.cli.scoreboard . --since \"6 months ago\""
    subprocess.run(git_scoreboard_direct_command, shell=True, check=True, capture_output=True, text=True, env=env)

    # 5. Run git-df with a remote repo
    git_df_remote_command = "python -m git_dataframe_tools.cli.git_df --remote-url https://github.com/pallets/flask --remote-branch main --output remote_commits.parquet --since \"1 year ago\""
    subprocess.run(git_df_remote_command, shell=True, check=True, capture_output=True, text=True, env=env)

    # 6. Run git-scoreboard with a remote repo
    git_scoreboard_remote_command = "python -m git_dataframe_tools.cli.scoreboard --remote-url https://github.com/pallets/flask --remote-branch main --since \"6 months ago\""
    subprocess.run(git_scoreboard_remote_command, shell=True, check=True, capture_output=True, text=True, env=env)