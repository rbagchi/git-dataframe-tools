import subprocess
import sys
from typing import Optional


def _run_git_command(cmd_args: list[str], cwd: Optional[str] = None) -> str:
    """
    Runs a git command and returns its stdout.
    Handles common git execution errors.
    """
    full_cmd = ["git"] + cmd_args
    try:
        process = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="ignore",
            cwd=cwd,
        )
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {' '.join(full_cmd)}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(
            "Error: 'git' command not found. Please ensure Git is installed and in your PATH."
        )
        sys.exit(1)
