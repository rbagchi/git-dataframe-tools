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

@patch('git2df.git_cli_utils.subprocess.run')
def test_git_cli_backend_get_raw_log_output_with_since_until(mock_subprocess_run):
    """Test GitCliBackend.get_raw_log_output with since and until arguments."""
    mock_subprocess_run.return_value.stdout = "filtered mocked output"
    mock_subprocess_run.return_value.strip.return_value = "filtered mocked output"
    
    backend = GitCliBackend()
    repo_path = "/filtered/repo"
    log_args = ["--author=test"]
    since_arg = "1.week ago"
    until_arg = "yesterday"
    
    output = backend.get_raw_log_output(repo_path, log_args=log_args, since=since_arg, until=until_arg)
    
    mock_subprocess_run.assert_called_once_with(
        ["git", "log", "--author=test", f"--since={since_arg}", f"--until={until_arg}"],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
        cwd=repo_path
    )
    assert output == "filtered mocked output"

@patch('git2df.git_cli_utils.subprocess.run')
def test_git_cli_backend_get_raw_log_output_with_all_filters(mock_subprocess_run):
    """Test GitCliBackend.get_raw_log_output with all filter arguments."""
    mock_subprocess_run.return_value.stdout = "all filters mocked output"
    mock_subprocess_run.return_value.strip.return_value = "all filters mocked output"
    
    backend = GitCliBackend()
    repo_path = "/all/filters/repo"
    since_arg = "2.days ago"
    until_arg = "now"
    author_arg = "Jane Doe"
    grep_arg = "feature"
    
    output = backend.get_raw_log_output(repo_path, since=since_arg, until=until_arg, author=author_arg, grep=grep_arg)
    
    mock_subprocess_run.assert_called_once_with(
        ["git", "log", f"--since={since_arg}", f"--until={until_arg}", f"--author={author_arg}", f"--grep={grep_arg}"],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
        cwd=repo_path
    )
    assert output == "all filters mocked output"

@patch('git2df.backends.GitCliBackend._get_default_branch', return_value='main')
@patch('git2df.git_cli_utils.subprocess.run')
def test_git_cli_backend_get_raw_log_output_with_all_filters_and_paths(mock_subprocess_run, mock_get_default_branch):
    """Test GitCliBackend.get_raw_log_output with all filter arguments including merged_only and paths."""
    mock_subprocess_run.return_value.stdout = "all filters and paths mocked output"
    mock_subprocess_run.return_value.strip.return_value = "all filters and paths mocked output"
    
    backend = GitCliBackend()
    repo_path = "/all/filters/paths/repo"
    since_arg = "3.days ago"
    until_arg = "now"
    author_arg = "Alice"
    grep_arg = "bugfix"
    merged_only_arg = True
    include_paths_arg = ["src/", "docs/"]
    exclude_paths_arg = ["tests/"]
    
    output = backend.get_raw_log_output(repo_path, since=since_arg, until=until_arg, 
                                         author=author_arg, grep=grep_arg, 
                                         merged_only=merged_only_arg, 
                                         include_paths=include_paths_arg, 
                                         exclude_paths=exclude_paths_arg)
    
    expected_cmd = [
        "git", "log", 
        f"--since={since_arg}", f"--until={until_arg}", 
        f"--author={author_arg}", f"--grep={grep_arg}",
        "--merges", "origin/main",
        "--", "src/", "docs/",
        ":(exclude)tests/"
    ]
    mock_subprocess_run.assert_called_once_with(
        expected_cmd,
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
        cwd=repo_path
    )
    assert output == "all filters and paths mocked output"
