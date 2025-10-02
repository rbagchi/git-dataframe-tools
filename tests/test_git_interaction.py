import pytest
from unittest.mock import patch, MagicMock, call
import subprocess
import sys
import pandas as pd

from git_scoreboard.config_models import GitAnalysisConfig, print_error, Colors
from git_scoreboard.git_utils import get_git_data_from_config

CONFIG_MODELS_MODULE_PATH = "git_scoreboard.config_models"
GIT_UTILS_MODULE_PATH = "git_scoreboard.git_utils"


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



# Test cases for get_git_data_from_config
@patch(f'{GIT_UTILS_MODULE_PATH}.get_commits_df')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo', return_value=True)
def test_get_git_data_from_config_default(mock_check_git_repo, mock_get_commits_df):
    mock_df = pd.DataFrame({
        'hash': ['a1b2c3d4'],
        'author_name': ['Test User'],
        'commit_date': [pd.Timestamp('2025-01-15')],
        'message': ['Initial commit']
    })
    mock_get_commits_df.return_value = mock_df
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    result_df = get_git_data_from_config(config, repo_path=".")
    pd.testing.assert_frame_equal(result_df, mock_df)
    mock_get_commits_df.assert_called_once_with(
        repo_path=".",
        since="2025-01-01",
        until="2025-01-31",
        author=None,
        merged_only=False,
        include_paths=None,
        exclude_paths=None
    )


@patch(f'{GIT_UTILS_MODULE_PATH}.get_commits_df')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo', return_value=True)
def test_get_git_data_from_config_merged_only(mock_check_git_repo, mock_get_commits_df):
    mock_df = pd.DataFrame({
        'hash': ['e5f6g7h8'],
        'author_name': ['Merge User'],
        'commit_date': [pd.Timestamp('2025-01-20')],
        'message': ['Merge branch feature/x']
    })
    mock_get_commits_df.return_value = mock_df
    config = GitAnalysisConfig(
        start_date="2025-01-01", end_date="2025-01-31", merged_only=True
    )
    result_df = get_git_data_from_config(config, repo_path=".")
    pd.testing.assert_frame_equal(result_df, mock_df)
    mock_get_commits_df.assert_called_once_with(
        repo_path=".",
        since="2025-01-01",
        until="2025-01-31",
        author=None,
        merged_only=True,
        include_paths=None,
        exclude_paths=None
    )


@patch(f'{GIT_UTILS_MODULE_PATH}.get_commits_df')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo', return_value=True)
def test_get_git_data_from_config_include_paths(mock_check_git_repo, mock_get_commits_df):
    mock_df = pd.DataFrame({
        'hash': ['f9g0h1i2'],
        'author_name': ['Path User'],
        'commit_date': [pd.Timestamp('2025-01-25')],
        'message': ['Add frontend feature']
    })
    mock_get_commits_df.return_value = mock_df
    config = GitAnalysisConfig(
        start_date="2025-01-01",
        end_date="2025-01-31",
        include_paths=["src/frontend", "src/backend"],
    )
    result_df = get_git_data_from_config(config, repo_path=".")
    pd.testing.assert_frame_equal(result_df, mock_df)
    mock_get_commits_df.assert_called_once_with(
        repo_path=".",
        since="2025-01-01",
        until="2025-01-31",
        author=None,
        merged_only=False,
        include_paths=["src/frontend", "src/backend"],
        exclude_paths=None
    )


@patch(f'{GIT_UTILS_MODULE_PATH}.get_commits_df')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo', return_value=True)
def test_get_git_data_from_config_exclude_paths(mock_check_git_repo, mock_get_commits_df):
    mock_df = pd.DataFrame({
        'hash': ['j3k4l5m6'],
        'author_name': ['Doc Writer'],
        'commit_date': [pd.Timestamp('2025-01-28')],
        'message': ['Update documentation']
    })
    mock_get_commits_df.return_value = mock_df
    config = GitAnalysisConfig(
        start_date="2025-01-01", end_date="2025-01-31", exclude_paths=["docs", "tests"]
    )
    result_df = get_git_data_from_config(config, repo_path=".")
    pd.testing.assert_frame_equal(result_df, mock_df)
    mock_get_commits_df.assert_called_once_with(
        repo_path=".",
        since="2025-01-01",
        until="2025-01-31",
        author=None,
        merged_only=False,
        include_paths=None,
        exclude_paths=["docs", "tests"]
    )


@patch(f'{GIT_UTILS_MODULE_PATH}.get_commits_df')
@patch(f'{GIT_UTILS_MODULE_PATH}.print_error')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo', return_value=True)
def test_get_git_data_from_config_error(mock_check_git_repo, mock_print_error, mock_get_commits_df):
    mock_get_commits_df.side_effect = Exception("Git command failed")
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    with pytest.raises(SystemExit) as excinfo:
        get_git_data_from_config(config, repo_path=".")
    assert excinfo.value.code == 1
    mock_print_error.assert_called_once_with("Error fetching git log data: Git command failed")


@patch(f'{GIT_UTILS_MODULE_PATH}.get_commits_df')
@patch(f'git_scoreboard.scoreboard.TQDM_AVAILABLE', False)
@patch(f'{CONFIG_MODELS_MODULE_PATH}.print_success')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.GitAnalysisConfig._check_git_repo', return_value=True)
def test_get_git_data_from_config_progress_bar_tqdm_not_available(
    mock_check_git_repo, mock_print_success, mock_get_commits_df
):
    mock_df = pd.DataFrame({
        'hash': ['n7o8p9q0'],
        'author_name': ['Many Commits User'],
        'commit_date': [pd.Timestamp('2025-01-10')],
        'message': ['Many commits']
    })
    mock_get_commits_df.return_value = mock_df
    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-01-31")
    result_df = get_git_data_from_config(config, repo_path=".")
    pd.testing.assert_frame_equal(result_df, mock_df)
    mock_get_commits_df.assert_called_once_with(
        repo_path=".",
        since="2025-01-01",
        until="2025-01-31",
        author=None,
        merged_only=False,
        include_paths=None,
        exclude_paths=None
    )




