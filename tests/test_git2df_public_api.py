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
    mock_backend_instance.get_raw_log_output.assert_called_once_with(
        repo_path, 
        ['--numstat', '--pretty=format:--%H--%an--%ae--%ad--%s', '--date=iso'],
        since=None, until=None, author=None, grep=None, 
        merged_only=False, include_paths=None, exclude_paths=None
    )
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
    mock_backend_instance.get_raw_log_output.assert_called_once_with(
        repo_path, 
        ['--numstat', '--pretty=format:--%H--%an--%ae--%ad--%s', '--date=iso', "--since=2.weeks", "--grep=feature"],
        since=None, until=None, author=None, grep=None,
        merged_only=False, include_paths=None, exclude_paths=None
    )
    mock_parse_git_data_internal.assert_called_once_with(["mocked raw git log output with filters"])
    mock_build_commits_df.assert_called_once_with(mock_parse_git_data_internal.return_value)
    assert df.equals(mock_df)

@patch('git2df.build_commits_df')
@patch('git2df._parse_git_data_internal')
@patch('git2df.GitCliBackend')
def test_get_commits_df_with_all_filters(mock_git_cli_backend, mock_parse_git_data_internal, mock_build_commits_df):
    """Test get_commits_df with all filter arguments applied."""
    # Setup mocks
    mock_backend_instance = MagicMock()
    mock_git_cli_backend.return_value = mock_backend_instance
    mock_backend_instance.get_raw_log_output.return_value = "mocked raw git log output with all filters"

    mock_parse_git_data_internal.return_value = defaultdict(lambda: {})

    mock_df = pd.DataFrame({
        'author_name': ['Author Three'],
        'author_email': ['author3@example.com'],
        'added': [30],
        'deleted': [15],
        'total_diff': [45],
        'num_commits': [3],
        'commit_hashes': [['hash3a', 'hash3b', 'hash3c']]
    })
    mock_build_commits_df.return_value = mock_df

    repo_path = "/test/all_filters_repo"
    since_arg = "3.days ago"
    until_arg = "today"
    author_arg = "Alice"
    grep_arg = "bugfix"
    
    # Call the function under test
    df = get_commits_df(repo_path, since=since_arg, until=until_arg, author=author_arg, grep=grep_arg)

    # Assertions
    mock_git_cli_backend.assert_called_once_with()
    mock_backend_instance.get_raw_log_output.assert_called_once_with(
        repo_path, 
        ['--numstat', '--pretty=format:--%H--%an--%ae--%ad--%s', '--date=iso'], 
        since=since_arg, until=until_arg, author=author_arg, grep=grep_arg,
        merged_only=False, include_paths=None, exclude_paths=None
    )
    mock_parse_git_data_internal.assert_called_once_with(["mocked raw git log output with all filters"])
    mock_build_commits_df.assert_called_once_with(mock_parse_git_data_internal.return_value)
    assert df.equals(mock_df)

@patch('git2df.build_commits_df')
@patch('git2df._parse_git_data_internal')
@patch('git2df.GitCliBackend')
def test_get_commits_df_with_all_filters_and_paths(mock_git_cli_backend, mock_parse_git_data_internal, mock_build_commits_df):
    """Test get_commits_df with all filter arguments including merged_only and paths."""
    # Setup mocks
    mock_backend_instance = MagicMock()
    mock_git_cli_backend.return_value = mock_backend_instance
    mock_backend_instance.get_raw_log_output.return_value = "mocked raw git log output with all filters and paths"

    mock_parse_git_data_internal.return_value = defaultdict(lambda: {})

    mock_df = pd.DataFrame({
        'author_name': ['Author Four'],
        'author_email': ['author4@example.com'],
        'added': [40],
        'deleted': [20],
        'total_diff': [60],
        'num_commits': [4],
        'commit_hashes': [['hash4a', 'hash4b', 'hash4c', 'hash4d']]
    })
    mock_build_commits_df.return_value = mock_df

    repo_path = "/test/all_filters_paths_repo"
    since_arg = "4.days ago"
    until_arg = "yesterday"
    author_arg = "Bob"
    grep_arg = "refactor"
    merged_only_arg = True
    include_paths_arg = ["app/", "lib/"]
    exclude_paths_arg = ["tests/"]
    
    # Call the function under test
    df = get_commits_df(repo_path, since=since_arg, until=until_arg, 
                        author=author_arg, grep=grep_arg, 
                        merged_only=merged_only_arg, 
                        include_paths=include_paths_arg, 
                        exclude_paths=exclude_paths_arg)

    # Assertions
    mock_git_cli_backend.assert_called_once_with()
    mock_backend_instance.get_raw_log_output.assert_called_once_with(
        repo_path, 
        ['--numstat', '--pretty=format:--%H--%an--%ae--%ad--%s', '--date=iso'], 
        since=since_arg, until=until_arg, author=author_arg, grep=grep_arg,
        merged_only=merged_only_arg, include_paths=include_paths_arg, exclude_paths=exclude_paths_arg
    )
    mock_parse_git_data_internal.assert_called_once_with(["mocked raw git log output with all filters and paths"])
    mock_build_commits_df.assert_called_once_with(mock_parse_git_data_internal.return_value)
    assert df.equals(mock_df)
