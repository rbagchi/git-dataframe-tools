from unittest.mock import patch, MagicMock
import subprocess

from git_scoreboard.config_models import GitAnalysisConfig

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
    GitAnalysisConfig(use_current_user=True) # Call constructor for side effects
    mock_print_error.assert_called_once_with("Error: Could not retrieve git user.name or user.email. Please configure git or run without --me.")
    mock_exit.assert_called_once_with(1)



