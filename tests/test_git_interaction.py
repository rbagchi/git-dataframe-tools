from unittest.mock import patch, MagicMock
import pytest
from git import InvalidGitRepositoryError, GitCommandError

from git_dataframe_tools.config_models import GitAnalysisConfig

CONFIG_MODELS_MODULE_PATH = "git_dataframe_tools.config_models"


@patch(f"{CONFIG_MODELS_MODULE_PATH}.git.Repo")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo")
def test_get_current_git_user_success(mock_check_git_repo, mock_repo):
    mock_check_git_repo.return_value = True
    mock_reader = MagicMock()
    mock_reader.get_value.side_effect = ["Test User", "test@example.com"]
    mock_repo_instance = MagicMock()
    mock_repo_instance.config_reader.return_value = mock_reader
    mock_repo.return_value = mock_repo_instance

    config = GitAnalysisConfig(use_current_user=True)

    assert config.current_user_name == "Test User"
    assert config.current_user_email == "test@example.com"
    assert mock_reader.get_value.call_count == 2


@patch(f"{CONFIG_MODELS_MODULE_PATH}.git.Repo")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo")
def test_get_current_git_user_no_name(mock_check_git_repo, mock_repo):
    mock_check_git_repo.return_value = True
    mock_reader = MagicMock()
    mock_reader.get_value.side_effect = ["", "test@example.com"]
    mock_repo_instance = MagicMock()
    mock_repo_instance.config_reader.return_value = mock_reader
    mock_repo.return_value = mock_repo_instance

    config = GitAnalysisConfig(use_current_user=True)

    assert config.current_user_name == ""
    assert config.current_user_email == "test@example.com"


@patch(f"{CONFIG_MODELS_MODULE_PATH}.git.Repo")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo")
def test_get_current_git_user_no_email(mock_check_git_repo, mock_repo):
    mock_check_git_repo.return_value = True
    mock_reader = MagicMock()
    mock_reader.get_value.side_effect = ["Test User", ""]
    mock_repo_instance = MagicMock()
    mock_repo_instance.config_reader.return_value = mock_reader
    mock_repo.return_value = mock_repo_instance

    config = GitAnalysisConfig(use_current_user=True)

    assert config.current_user_name == "Test User"
    assert config.current_user_email == ""


@pytest.mark.parametrize(
    "raised_exception",
    [InvalidGitRepositoryError, GitCommandError("git config", 1, b"", b""), KeyError],
)
@patch(f"{CONFIG_MODELS_MODULE_PATH}.print_error")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.sys.exit")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.git.Repo")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo")
def test_get_current_git_user_failure(
    mock_check_git_repo, mock_repo, mock_exit, mock_print_error, raised_exception
):
    mock_check_git_repo.return_value = True
    mock_repo.side_effect = raised_exception

    GitAnalysisConfig(use_current_user=True)

    mock_print_error.assert_called_once_with(
        "Error: Could not retrieve git user.name or user.email. Please configure git or run without --me."
    )
    mock_exit.assert_called_once_with(1)
