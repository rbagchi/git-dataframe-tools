import pytest
import subprocess
from git2df.git_cli_utils import _run_git_command

def test_run_git_command_success():
    """Test _run_git_command with a successful git command."""
    # This command should always succeed in a git repository
    output = _run_git_command(["rev-parse", "--is-inside-work-tree"])
    assert output.strip() == "true"

def test_run_git_command_failure():
    """Test _run_git_command with a failing git command."""
    with pytest.raises(SystemExit) as excinfo:
        _run_git_command(["non-existent-command"])
    assert excinfo.value.code == 1

def test_run_git_command_non_git_dir(tmp_path):
    """Test _run_git_command in a non-git directory."""
    # Create a temporary directory that is not a git repo
    non_git_dir = tmp_path / "non_git_repo"
    non_git_dir.mkdir()

    with pytest.raises(SystemExit) as excinfo:
        _run_git_command(["rev-parse", "--is-inside-work-tree"], cwd=str(non_git_dir))
    assert excinfo.value.code == 1
