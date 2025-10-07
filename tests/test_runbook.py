import pytest
import os
import subprocess
import re
from pathlib import Path

def extract_code_blocks(markdown_file):
    with open(markdown_file, 'r') as f:
        content = f.read()
    code_blocks = re.findall(r"```bash\n(.*?)\n```", content, re.DOTALL)
    return code_blocks

@pytest.mark.parametrize("code", extract_code_blocks('RUNBOOK-git2df.md'))
def test_runbook_code(code, tmp_path: Path):
    # Create a dummy git repository in the temporary directory
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    (tmp_path / "file1.txt").write_text("file1 content")
    subprocess.run(["git", "add", "file1.txt"], check=True)
    subprocess_env = os.environ.copy()
    subprocess_env["GIT_COMMITTER_DATE"] = "2023-01-01T12:00:00+00:00"
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, env=subprocess_env)
    (tmp_path / "file1.txt").write_text("file1 content updated")
    subprocess.run(["git", "add", "file1.txt"], check=True)
    subprocess_env["GIT_COMMITTER_DATE"] = "2023-06-15T12:00:00+00:00"
    subprocess.run(["git", "commit", "-m", "Update file1"], check=True, env=subprocess_env)
    (tmp_path / "file2.txt").write_text("file2 content")
    subprocess.run(["git", "add", "file2.txt"], check=True)
    subprocess_env["GIT_COMMITTER_DATE"] = "2023-12-01T12:00:00+00:00"
    subprocess.run(["git", "commit", "-m", "Add file2"], check=True, env=subprocess_env)

    try:
        # Set PYTHONPATH to include the project root so git2df can be found
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent)
        subprocess.run(code, shell=True, check=True, capture_output=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Code block failed: {code}\nStdout: {e.stdout}\nStderr: {e.stderr}")
