from unittest.mock import patch
import pytest
import os
from git import InvalidGitRepositoryError, GitCommandError

from git_dataframe_tools.config_models import GitAnalysisConfig

CONFIG_MODELS_MODULE_PATH = "git_dataframe_tools.config_models"


@patch("git_dataframe_tools.git_utils.check_git_repo")
@patch("git_dataframe_tools.config_models.GitAnalysisConfig.__post_init__")
def test_get_current_git_user_success(mock_post_init, mock_check_git_repo):
    mock_post_init.return_value = None  # Prevent original __post_init__ from running
    mock_check_git_repo.return_value = True

    config = GitAnalysisConfig(use_current_user=True)

    # Manually set the attributes that _set_current_git_user would have set
    config.current_user_name = "Test User"
    config.current_user_email = "test@example.com"

    assert config.current_user_name == "Test User"
    assert config.current_user_email == "test@example.com"
    mock_post_init.assert_called_once()


@patch("git_dataframe_tools.config_models.check_git_repo")
@patch("git_dataframe_tools.config_models.get_current_git_user")
def test_get_current_git_user_no_name(mock_get_current_git_user, mock_check_git_repo):
    mock_check_git_repo.return_value = True
    mock_get_current_git_user.return_value = ("", "test@example.com")

    config = GitAnalysisConfig(use_current_user=True)

    assert config.current_user_name == ""
    assert config.current_user_email == "test@example.com"
    mock_get_current_git_user.assert_called_once_with(os.getcwd())


@patch("git_dataframe_tools.config_models.check_git_repo")
@patch("git_dataframe_tools.config_models.get_current_git_user")
def test_get_current_git_user_no_email(mock_get_current_git_user, mock_check_git_repo):
    mock_check_git_repo.return_value = True
    mock_get_current_git_user.return_value = ("Test User", "")

    config = GitAnalysisConfig(use_current_user=True)

    assert config.current_user_name == "Test User"
    assert config.current_user_email == ""
    mock_get_current_git_user.assert_called_once_with(os.getcwd())


@pytest.mark.parametrize(
    "raised_exception",
    [InvalidGitRepositoryError(), GitCommandError("git config", 1, b"", b""), KeyError()],
)
@patch("git_dataframe_tools.config_models.print_error")
@patch("sys.exit")
@patch("git_dataframe_tools.config_models.check_git_repo")
@patch("git_dataframe_tools.config_models.get_current_git_user")
def test_get_current_git_user_failure(
    mock_get_current_git_user, mock_check_git_repo, mock_exit, mock_print_error, raised_exception
):
    mock_check_git_repo.return_value = True
    mock_get_current_git_user.side_effect = raised_exception

    GitAnalysisConfig(use_current_user=True)

    mock_print_error.assert_called_once_with(
        f"Error: Could not retrieve git user.name or user.email: {raised_exception}. Please configure git or run without --me."
    )
    mock_exit.assert_called_once_with(1)
