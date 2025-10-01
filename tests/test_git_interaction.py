import pytest
from unittest.mock import patch, MagicMock
import subprocess
import sys

# Assuming scoreboard.py is in the parent directory
sys.path.insert(0, './')
from scoreboard import GitAnalysisConfig, check_git_repo, print_error

# Test cases for check_git_repo
@patch('scoreboard.subprocess.run')
def test_check_git_repo_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    assert check_git_repo() is True
    mock_run.assert_called_once_with(['git', 'rev-parse', '--git-dir'], capture_output=True, check=True)

@patch('scoreboard.subprocess.run')
def test_check_git_repo_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, 'git rev-parse')
    assert check_git_repo() is False
    mock_run.assert_called_once_with(['git', 'rev-parse', '--git-dir'], capture_output=True, check=True)

# Test cases for GitAnalysisConfig._get_current_git_user
@patch('scoreboard.subprocess.run')
def test_get_current_git_user_success(mock_run):
    mock_run.side_effect = [
        MagicMock(stdout="Test User\n", returncode=0),  # git config user.name
        MagicMock(stdout="test@example.com\n", returncode=0) # git config user.email
    ]
    config = GitAnalysisConfig()
    name, email = config._get_current_git_user()
    assert name == "Test User"
    assert email == "test@example.com"
    assert mock_run.call_count == 2

@patch('scoreboard.subprocess.run')
def test_get_current_git_user_no_name(mock_run):
    mock_run.side_effect = [
        MagicMock(stdout="\n", returncode=0),  # git config user.name (empty)
        MagicMock(stdout="test@example.com\n", returncode=0) # git config user.email
    ]
    config = GitAnalysisConfig()
    name, email = config._get_current_git_user()
    assert name == ""
    assert email == "test@example.com"

@patch('scoreboard.subprocess.run')
def test_get_current_git_user_no_email(mock_run):
    mock_run.side_effect = [
        MagicMock(stdout="Test User\n", returncode=0),  # git config user.name
        MagicMock(stdout="\n", returncode=0) # git config user.email (empty)
    ]
    config = GitAnalysisConfig()
    name, email = config._get_current_git_user()
    assert name == "Test User"
    assert email == ""

@patch('scoreboard.subprocess.run')
def test_get_current_git_user_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, 'git config user.name')
    config = GitAnalysisConfig()
    name, email = config._get_current_git_user()
    assert name is None
    assert email is None
    mock_run.assert_called_once() # Only the first call should happen before exception

# Test cases for GitAnalysisConfig._get_main_branch
@patch('scoreboard.subprocess.run')
def test_get_main_branch_origin_main(mock_run):
    mock_run.side_effect = [
        MagicMock(returncode=0), # git rev-parse --verify origin/main
        subprocess.CalledProcessError(1, 'git rev-parse'), # git rev-parse --verify origin/master
        subprocess.CalledProcessError(1, 'git symbolic-ref') # git symbolic-ref
    ]
    config = GitAnalysisConfig()
    assert config._get_main_branch() == 'origin/main'
    assert mock_run.call_count == 1 # Only origin/main check should run

@patch('scoreboard.subprocess.run')
def test_get_main_branch_origin_master(mock_run):
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, 'git rev-parse'), # git rev-parse --verify origin/main
        MagicMock(returncode=0), # git rev-parse --verify origin/master
        subprocess.CalledProcessError(1, 'git symbolic-ref') # git symbolic-ref
    ]
    config = GitAnalysisConfig()
    assert config._get_main_branch() == 'origin/master'
    assert mock_run.call_count == 2 # origin/main and origin/master checks should run

@patch('scoreboard.subprocess.run')
def test_get_main_branch_symbolic_ref(mock_run):
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, 'git rev-parse'), # git rev-parse --verify origin/main
        subprocess.CalledProcessError(1, 'git rev-parse'), # git rev-parse --verify origin/master
        MagicMock(stdout="refs/remotes/origin/some_branch\n", returncode=0) # git symbolic-ref
    ]
    config = GitAnalysisConfig()
    assert config._get_main_branch() == 'origin/some_branch'
    assert mock_run.call_count == 3 # All three checks should run

@patch('scoreboard.subprocess.run')
def test_get_main_branch_not_found(mock_run):
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, 'git rev-parse'), # git rev-parse --verify origin/main
        subprocess.CalledProcessError(1, 'git rev-parse'), # git rev-parse --verify origin/master
        subprocess.CalledProcessError(1, 'git symbolic-ref') # git symbolic-ref
    ]
    config = GitAnalysisConfig()
    assert config._get_main_branch() is None
    assert mock_run.call_count == 3 # All three checks should run


# Test cases for GitAnalysisConfig._estimate_commit_count
@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
def test_estimate_commit_count_default(mock_get_main_branch, mock_run):
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="123\n", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config._estimate_commit_count() == 123
    mock_run.assert_called_once_with(
        ['git', 'rev-list', '--count', 'HEAD', '--since=2025-01-01', '--until=2025-01-31'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
def test_estimate_commit_count_merged_only(mock_get_main_branch, mock_run):
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="456\n", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31", merged_only=True)
    assert config._estimate_commit_count() == 456
    mock_run.assert_called_once_with(
        ['git', 'rev-list', '--count', 'origin/main', '--since=2025-01-01', '--until=2025-01-31'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
def test_estimate_commit_count_merged_only_no_main_branch(mock_get_main_branch, mock_run):
    mock_get_main_branch.return_value = None
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31", merged_only=True)
    assert config._estimate_commit_count() is None
    mock_run.assert_not_called()

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
def test_estimate_commit_count_error(mock_get_main_branch, mock_run):
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.side_effect = subprocess.CalledProcessError(1, 'git rev-list')
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config._estimate_commit_count() is None
    mock_run.assert_called_once()

# Test cases for GitAnalysisConfig.get_git_log_data
@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
@patch('scoreboard.GitAnalysisConfig._estimate_commit_count')
def test_get_git_log_data_default(mock_estimate_commit_count, mock_get_main_branch, mock_run):
    mock_estimate_commit_count.return_value = None # Don't trigger progress bar
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="git log output", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config.get_git_log_data() == "git log output"
    mock_run.assert_called_once_with(
        ['git', 'log', '--since=2025-01-01', '--until=2025-01-31', '--pretty=format:%H|%an|%ae', '--numstat'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
@patch('scoreboard.GitAnalysisConfig._estimate_commit_count')
def test_get_git_log_data_merged_only(mock_estimate_commit_count, mock_get_main_branch, mock_run):
    mock_estimate_commit_count.return_value = None # Don't trigger progress bar
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="git log output merged", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31", merged_only=True)
    assert config.get_git_log_data() == "git log output merged"
    mock_run.assert_called_once_with(
        ['git', 'log', 'origin/main', '--since=2025-01-01', '--until=2025-01-31', '--pretty=format:%H|%an|%ae', '--numstat'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
@patch('scoreboard.GitAnalysisConfig._estimate_commit_count')
def test_get_git_log_data_include_paths(mock_estimate_commit_count, mock_get_main_branch, mock_run):
    mock_estimate_commit_count.return_value = None
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="git log output include", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31", include_paths=["src/frontend", "src/backend"])
    assert config.get_git_log_data() == "git log output include"
    mock_run.assert_called_once_with(
        ['git', 'log', '--since=2025-01-01', '--until=2025-01-31', '--pretty=format:%H|%an|%ae', '--numstat', '--', 'src/frontend', 'src/backend'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
@patch('scoreboard.GitAnalysisConfig._estimate_commit_count')
def test_get_git_log_data_exclude_paths(mock_estimate_commit_count, mock_get_main_branch, mock_run):
    mock_estimate_commit_count.return_value = None
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="git log output exclude", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31", exclude_paths=["docs", "tests"])
    assert config.get_git_log_data() == "git log output exclude"
    mock_run.assert_called_once_with(
        ['git', 'log', '--since=2025-01-01', '--until=2025-01-31', '--pretty=format:%H|%an|%ae', '--numstat', '--', ':!docs', ':!tests'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
@patch('scoreboard.GitAnalysisConfig._estimate_commit_count')
def test_get_git_log_data_error(mock_estimate_commit_count, mock_get_main_branch, mock_run):
    mock_estimate_commit_count.return_value = None
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.side_effect = subprocess.CalledProcessError(1, 'git log')
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    with pytest.raises(SystemExit) as excinfo:
        config.get_git_log_data()
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
@patch('scoreboard.GitAnalysisConfig._estimate_commit_count')
@patch('scoreboard.TQDM_AVAILABLE', False)
@patch('builtins.print')
def test_get_git_log_data_progress_bar_tqdm_not_available(mock_print, mock_estimate_commit_count, mock_get_main_branch, mock_run):
    mock_estimate_commit_count.return_value = 200 # Trigger progress bar logic
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="git log output with many commits", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config.get_git_log_data() == "git log output with many commits"
    mock_print.assert_any_call("\033[0;32mFetching 200 commits (this may take a while...)\033[0m")
    mock_run.assert_called_once()

# Test cases for GitAnalysisConfig.get_commit_summary
@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
def test_get_commit_summary_default(mock_get_main_branch, mock_run):
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="commit summary output", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config.get_commit_summary() == "commit summary output"
    mock_run.assert_called_once_with(
        ['git', 'shortlog', '--since=2025-01-01', '--until=2025-01-31', '--numbered', '--summary'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
def test_get_commit_summary_merged_only(mock_get_main_branch, mock_run):
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.return_value = MagicMock(stdout="commit summary output merged", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31", merged_only=True)
    assert config.get_commit_summary() == "commit summary output merged"
    mock_run.assert_called_once_with(
        ['git', 'shortlog', 'origin/main', '--since=2025-01-01', '--until=2025-01-31', '--numbered', '--summary'],
        capture_output=True, text=True, check=True
    )

@patch('scoreboard.subprocess.run')
@patch('scoreboard.GitAnalysisConfig._get_main_branch')
def test_get_commit_summary_error(mock_get_main_branch, mock_run):
    mock_get_main_branch.return_value = 'origin/main'
    mock_run.side_effect = subprocess.CalledProcessError(1, 'git shortlog')
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config.get_commit_summary() == "Could not generate commit summary"
    mock_run.assert_called_once()


