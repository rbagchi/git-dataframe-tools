from unittest.mock import patch
from git2df.backends import GitCliBackend

@patch('git2df.git_cli_utils.subprocess.run')
def test_git_cli_backend_get_raw_log_output(mock_subprocess_run):
    """Test GitCliBackend.get_raw_log_output method."""
    mock_subprocess_run.return_value.stdout = "mocked git log output"
    mock_subprocess_run.return_value.strip.return_value = "mocked git log output"
    
    backend = GitCliBackend()
    repo_path = "/test/repo"
    log_args = ["--since=1.day", "--author=test"]
    
    output = backend.get_raw_log_output(repo_path, log_args)
    
    mock_subprocess_run.assert_called_once_with(
        ["git", "log"] + log_args,
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
        cwd=repo_path
    )
    assert output == "mocked git log output"

@patch('git2df.git_cli_utils.subprocess.run')
def test_git_cli_backend_get_raw_log_output_empty_args(mock_subprocess_run):
    """Test GitCliBackend.get_raw_log_output with empty log arguments."""
    mock_subprocess_run.return_value.stdout = "another mocked output"
    mock_subprocess_run.return_value.strip.return_value = "another mocked output"
    
    backend = GitCliBackend()
    repo_path = "/another/repo"
    log_args = []
    
    output = backend.get_raw_log_output(repo_path, log_args)
    
    mock_subprocess_run.assert_called_once_with(
        ["git", "log"],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
        cwd=repo_path
    )
    assert output == "another mocked output"
