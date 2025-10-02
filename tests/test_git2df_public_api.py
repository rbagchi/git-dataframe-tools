import pandas as pd
from unittest.mock import patch, MagicMock
from git2df import get_commits_df
from collections import defaultdict

@patch('git2df.build_commits_df')
@patch('git2df._parse_git_data_internal')
@patch('git2df.GitCliBackend')
def test_get_commits_df_no_filters(mock_git_cli_backend, mock_parse_git_data_internal, mock_build_commits_df):
    """Test get_commits_df with no filters applied."""
    # Setup mocks
    mock_backend_instance = MagicMock()
    mock_git_cli_backend.return_value = mock_backend_instance
    mock_backend_instance.get_raw_log_output.return_value = "mocked raw git log output"

    mock_parse_git_data_internal.return_value = defaultdict(lambda: {})

    mock_df = pd.DataFrame({
        'author_name': ['Author One'],
        'author_email': ['author1@example.com'],
        'added': [10],
        'deleted': [5],
        'total_diff': [15],
        'num_commits': [1],
        'commit_hashes': [['hash1']]
    })
    mock_build_commits_df.return_value = mock_df

    repo_path = "/test/repo"
    
    # Call the function under test
    df = get_commits_df(repo_path)

    # Assertions
    mock_git_cli_backend.assert_called_once_with()
    mock_backend_instance.get_raw_log_output.assert_called_once_with(repo_path, [])
    mock_parse_git_data_internal.assert_called_once_with(["mocked raw git log output"])
    mock_build_commits_df.assert_called_once_with(mock_parse_git_data_internal.return_value)
    assert df.equals(mock_df)

@patch('git2df.build_commits_df')
@patch('git2df._parse_git_data_internal')
@patch('git2df.GitCliBackend')
def test_get_commits_df_with_filters(mock_git_cli_backend, mock_parse_git_data_internal, mock_build_commits_df):
    """Test get_commits_df with filters applied."""
    # Setup mocks
    mock_backend_instance = MagicMock()
    mock_git_cli_backend.return_value = mock_backend_instance
    mock_backend_instance.get_raw_log_output.return_value = "mocked raw git log output with filters"

    mock_parse_git_data_internal.return_value = defaultdict(lambda: {})

    mock_df = pd.DataFrame({
        'author_name': ['Author Two'],
        'author_email': ['author2@example.com'],
        'added': [20],
        'deleted': [10],
        'total_diff': [30],
        'num_commits': [2],
        'commit_hashes': [['hash2a', 'hash2b']]
    })
    mock_build_commits_df.return_value = mock_df

    repo_path = "/test/another_repo"
    log_args = ["--since=2.weeks", "--grep=feature"]
    
    # Call the function under test
    df = get_commits_df(repo_path, log_args=log_args)

    # Assertions
    mock_git_cli_backend.assert_called_once_with()
    mock_backend_instance.get_raw_log_output.assert_called_once_with(repo_path, log_args)
    mock_parse_git_data_internal.assert_called_once_with(["mocked raw git log output with filters"])
    mock_build_commits_df.assert_called_once_with(mock_parse_git_data_internal.return_value)
    assert df.equals(mock_df)
