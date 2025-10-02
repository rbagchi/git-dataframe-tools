import pytest
from unittest.mock import patch, MagicMock, call
import subprocess
import sys

# Assuming scoreboard.py is in the parent directory

from git_scoreboard.config_models import GitAnalysisConfig, print_error, Colors

CONFIG_MODELS_MODULE_PATH = "git_scoreboard.config_models"


# Test cases for GitAnalysisConfig._get_current_git_user
@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo')
def test_get_current_git_user_success(mock_check_git_repo, mock_run):
    mock_check_git_repo.return_value = True
    mock_run.side_effect = [
        MagicMock(stdout="Test User\n", returncode=0),  # git config user.name
        MagicMock(stdout="test@example.com\n", returncode=0),  # git config user.email
    ]
    config = GitAnalysisConfig(use_current_user=True)
    assert config.current_user_name == "Test User"
    assert config.current_user_email == "test@example.com"
    assert mock_run.call_count == 2


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo')
def test_get_current_git_user_no_name(mock_check_git_repo, mock_run):
    mock_check_git_repo.return_value = True
    mock_run.side_effect = [
        MagicMock(stdout="\n", returncode=0),  # git config user.name (empty)
        MagicMock(stdout="test@example.com\n", returncode=0),  # git config user.email
    ]
    config = GitAnalysisConfig(use_current_user=True)
    assert config.current_user_name == ""
    assert config.current_user_email == "test@example.com"


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo')
def test_get_current_git_user_no_email(mock_check_git_repo, mock_run):
    mock_check_git_repo.return_value = True
    mock_run.side_effect = [
        MagicMock(stdout="Test User\n", returncode=0),  # git config user.name
        MagicMock(stdout="\n", returncode=0),  # git config user.email (empty)
    ]
    config = GitAnalysisConfig(use_current_user=True)
    assert config.current_user_name == "Test User"
    assert config.current_user_email == ""


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_error')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.sys.exit')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo')
def test_get_current_git_user_failure(mock_check_git_repo, mock_exit, mock_print_error, mock_run):
    mock_check_git_repo.return_value = True
    mock_run.side_effect = subprocess.CalledProcessError(1, "git config user.name")
    config = GitAnalysisConfig(use_current_user=True)
    mock_print_error.assert_called_once_with("Error: Could not retrieve git user.name or user.email. Please configure git or run without --me.")
    mock_exit.assert_called_once_with(1)



# Test cases for GitAnalysisConfig.get_git_log_data
@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_warning')
def test_get_git_log_data_default(mock_print_warning, mock_run):
    mock_run.return_value = MagicMock(stdout="--git log output", returncode=0)
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config.get_git_log_data() == ['', 'git log output']
    mock_run.assert_called_once_with(
        [
            "git",
            "log",
            "--since=2025-01-01",
            "--until=2025-01-31",
            "--numstat",
            "--pretty=format:--%H--%an--%ae--%ad--%s",
            "--date=iso",
        ],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
    )
    mock_print_warning.assert_not_called()


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_warning')
def test_get_git_log_data_merged_only(mock_print_warning, mock_run):
    mock_run.side_effect = [
        MagicMock(returncode=0), # for checking main branch
        MagicMock(stdout="--git log output merged", returncode=0)
    ]
    config = GitAnalysisConfig(
        start_date="2025-01-01", end_date="2025-01-31", merged_only=True
    )
    assert config.get_git_log_data() == ['', 'git log output merged']
    mock_run.assert_called_with(
        [
            "git",
            "log",
            "--since=2025-01-01",
            "--until=2025-01-31",
            "--numstat",
            "--pretty=format:--%H--%an--%ae--%ad--%s",
            "--date=iso",
            "--merges",
            "origin/main",
        ],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
    )
    mock_print_warning.assert_not_called()


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_warning')
def test_get_git_log_data_include_paths(mock_print_warning, mock_run):
    mock_run.return_value = MagicMock(stdout="--git log output include", returncode=0)
    config = GitAnalysisConfig(
        start_date="2025-01-01",
        end_date="2025-01-31",
        include_paths=["src/frontend", "src/backend"],
    )
    assert config.get_git_log_data() == ['', 'git log output include']
    mock_run.assert_called_once_with(
        [
            "git",
            "log",
            "--since=2025-01-01",
            "--until=2025-01-31",
            "--numstat",
            "--pretty=format:--%H--%an--%ae--%ad--%s",
            "--date=iso",
            "--",
            "src/frontend",
            "src/backend",
        ],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
    )
    mock_print_warning.assert_not_called()


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_warning')
def test_get_git_log_data_exclude_paths(mock_print_warning, mock_run):
    mock_run.return_value = MagicMock(stdout="--git log output exclude", returncode=0)
    config = GitAnalysisConfig(
        start_date="2025-01-01", end_date="2025-01-31", exclude_paths=["docs", "tests"]
    )
    assert config.get_git_log_data() == ['', 'git log output exclude']
    mock_run.assert_called_once_with(
        [
            "git",
            "log",
            "--since=2025-01-01",
            "--until=2025-01-31",
            "--numstat",
            "--pretty=format:--%H--%an--%ae--%ad--%s",
            "--date=iso",
            ":(exclude)docs",
            ":(exclude)tests",
        ],
        capture_output=True,
        text=True,
        check=True,
        encoding='utf-8',
        errors='ignore',
    )
    mock_print_warning.assert_not_called()


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_error')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.sys.exit')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo')
def test_get_git_log_data_error(mock_check_git_repo, mock_exit, mock_print_error, mock_run):
    mock_check_git_repo.return_value = True
    mock_run.side_effect = subprocess.CalledProcessError(1, "git log", stderr="fatal: bad revision")
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    config.get_git_log_data()
    assert mock_print_error.call_args_list == [
        call("Error running git log: Command 'git log' returned non-zero exit status 1."),
        call("Stderr: fatal: bad revision")
    ]
    mock_exit.assert_called_once_with(1)


@patch(f'{CONFIG_MODELS_MODULE_PATH}.subprocess.run')
@patch(f'git_scoreboard.scoreboard.TQDM_AVAILABLE', False)
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_success')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo')
def test_get_git_log_data_progress_bar_tqdm_not_available(
    mock_check_git_repo, mock_print_success, mock_run
):
    mock_check_git_repo.return_value = True
    mock_run.return_value = MagicMock(
        stdout="--git log output with many commits", returncode=0
    )
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    assert config.get_git_log_data() == ['', 'git log output with many commits']
    mock_run.assert_called_once()




