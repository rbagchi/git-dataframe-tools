from unittest.mock import patch, MagicMock
import pytest
import os
from git import InvalidGitRepositoryError, GitCommandError
import typer

from git_dataframe_tools.config_models import GitAnalysisConfig

CONFIG_MODELS_MODULE_PATH = "git_dataframe_tools.config_models"


@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._set_date_range")
@patch(
    f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig.repo_info_provider",
    new_callable=MagicMock,
)
def test_get_current_git_user_success(mock_repo_info_provider, mock_set_date_range):
    mock_repo_info_provider.is_git_repo.return_value = True
    mock_repo_info_provider.get_current_user_info.return_value = (
        "Test User",
        "test@example.com",
    )

    config = GitAnalysisConfig(
        use_current_user=True, repo_info_provider=mock_repo_info_provider
    )

    assert config.current_user_name == "Test User"
    assert config.current_user_email == "test@example.com"
    mock_repo_info_provider.is_git_repo.assert_called_once_with(os.getcwd())
    mock_repo_info_provider.get_current_user_info.assert_called_once_with(os.getcwd())
    mock_set_date_range.assert_called_once()


@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._set_date_range")
@patch(
    f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig.repo_info_provider",
    new_callable=MagicMock,
)
def test_get_current_git_user_no_name(mock_repo_info_provider, mock_set_date_range):
    mock_repo_info_provider.is_git_repo.return_value = True
    mock_repo_info_provider.get_current_user_info.return_value = (
        "",
        "test@example.com",
    )

    config = GitAnalysisConfig(
        use_current_user=True, repo_info_provider=mock_repo_info_provider
    )

    assert config.current_user_name == ""
    assert config.current_user_email == "test@example.com"
    mock_repo_info_provider.is_git_repo.assert_called_once_with(os.getcwd())
    mock_repo_info_provider.get_current_user_info.assert_called_once_with(os.getcwd())
    mock_set_date_range.assert_called_once()


@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._set_date_range")
@patch(
    f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig.repo_info_provider",
    new_callable=MagicMock,
)
def test_get_current_git_user_no_email(mock_repo_info_provider, mock_set_date_range):
    mock_repo_info_provider.is_git_repo.return_value = True
    mock_repo_info_provider.get_current_user_info.return_value = ("Test User", "")

    config = GitAnalysisConfig(
        use_current_user=True, repo_info_provider=mock_repo_info_provider
    )

    assert config.current_user_name == "Test User"
    assert config.current_user_email == ""
    mock_repo_info_provider.is_git_repo.assert_called_once_with(os.getcwd())
    mock_repo_info_provider.get_current_user_info.assert_called_once_with(os.getcwd())
    mock_set_date_range.assert_called_once()


@pytest.mark.parametrize(
    "raised_exception",
    [
        InvalidGitRepositoryError(),
        GitCommandError("git config", 1, b"", b""),
        KeyError(),
    ],
)
@patch("loguru.logger.error")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._set_date_range")
@patch(
    f"{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig.repo_info_provider",
    new_callable=MagicMock,
)
def test_get_current_git_user_failure(
    mock_repo_info_provider,
    mock_set_date_range,
    mock_print_error,
    raised_exception,
):
    mock_repo_info_provider.is_git_repo.return_value = True
    mock_repo_info_provider.get_current_user_info.side_effect = raised_exception

    with pytest.raises(typer.BadParameter):
        GitAnalysisConfig(use_current_user=True, repo_info_provider=mock_repo_info_provider)

    mock_print_error.assert_called_once_with(
        f"Error: Could not retrieve git user.name or user.email: {raised_exception}. Please configure git or run without --me."
    )
    mock_repo_info_provider.is_git_repo.assert_called_once_with(os.getcwd())
    mock_repo_info_provider.get_current_user_info.assert_called_once_with(os.getcwd())
    mock_set_date_range.assert_called_once()
