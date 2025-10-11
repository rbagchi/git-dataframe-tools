import pytest
import os
import subprocess
from pathlib import Path
from tests.conftest import extract_code_blocks


def test_readme_commands(git_repo):
    project_root = Path(__file__).parent.parent
    readme_path = project_root / "README.md"

    # Extract commands before changing directory
    commands_from_readme = []
    for code in extract_code_blocks(readme_path, language="bash"):
        if "remote-url" in code:
            continue
        if "uv pip install" in code:
            continue
        commands_from_readme.extend(code.strip().split("\n"))

    # Change to the git_repo directory
    os.chdir(git_repo)

    # Install the project
    subprocess.run(
        ["uv", "pip", "install", "-e", str(project_root)],
        check=True,
        capture_output=True,
        text=True,
    )

    for command in commands_from_readme:
        if not command.strip():
            continue
        try:
            subprocess.run(
                command.replace("git-scoreboard .", "git-scoreboard --repo-path ."), shell=True, check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            pytest.fail(
                f"Command failed: {command}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            )
