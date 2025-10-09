import pytest
import os
import subprocess
from pathlib import Path
import sys
from tests.conftest import extract_code_blocks

@pytest.mark.parametrize("code", extract_code_blocks('RUNBOOK-git2df.md', language="python"))
def test_runbook_code(code, tmp_path: Path, git_repo):
    if "remote_url" in code:
        pytest.skip("Skipping remote repo test in runbook")

    # Change to the git_repo directory
    os.chdir(git_repo)

    # Create a temporary file to run the python code
    py_file = tmp_path / "runbook_code.py"
    py_file.write_text(code)

    try:
        # Set PYTHONPATH to include the project root so git2df can be found
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent)
        # Pass the git_repo path to the environment for the subprocess
        env["GIT_REPO_PATH"] = str(git_repo)
        subprocess.run([sys.executable, str(py_file)], shell=False, check=True, capture_output=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Code block failed: {code}\nStdout: {e.stdout}\nStderr: {e.stderr}")
