from unittest.mock import patch
import pytest
import pandas as pd
from git_dataframe_tools.cli.git_df import run_git_df_cli

# Mock data for get_commits_df
MOCKED_COMMITS_DF = pd.DataFrame(
    {
        "commit_hash": ["hash1"],
        "author_name": ["Author1"],
        "commit_date": [pd.Timestamp("2023-01-01")],
        "file_paths": ["file1.txt"],
        "additions": [10],
        "deletions": [5],
    }
)


class MockArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@patch("git_dataframe_tools.cli.git_df.setup_logging")
@patch("git_dataframe_tools.cli.git_df.os.path.isdir")
@patch("git_dataframe_tools.cli.git_df.get_commits_df")
@patch("git_dataframe_tools.cli.git_df.pq.write_table")
def test_run_git_df_cli_success(
    mock_write_table, mock_get_commits_df, mock_isdir, mock_setup_logging
):
    mock_isdir.return_value = True
    mock_get_commits_df.return_value = MOCKED_COMMITS_DF

    args = MockArgs(
        repo_path="/test/repo",
        remote_url=None,
        remote_branch="main",
        output="/test/output.parquet",
        since=None,
        until=None,
        author=None,
        grep=None,
        merges=False,
        path=None,
        exclude_path=None,
        debug=False,
        verbose=False,
    )

    run_git_df_cli(args)

    mock_setup_logging.assert_called_once_with(debug=False, verbose=False)
    mock_isdir.assert_called_once_with("/test/repo")
    mock_get_commits_df.assert_called_once_with(
        repo_path="/test/repo",
        remote_url=None,
        remote_branch="main",
        since=None,
        until=None,
        author=None,
        grep=None,
        merged_only=False,
        include_paths=None,
        exclude_paths=None,
    )
    mock_write_table.assert_called_once()


@patch("git_dataframe_tools.cli.git_df.setup_logging")
@patch("git_dataframe_tools.cli.git_df.os.path.isdir")
@patch("git_dataframe_tools.cli.git_df.get_commits_df")
@patch("git_dataframe_tools.cli.git_df.pq.write_table")
@patch("git_dataframe_tools.cli.git_df.sys.exit", side_effect=SystemExit)
def test_run_git_df_cli_repo_not_found(
    mock_sys_exit, mock_write_table, mock_get_commits_df, mock_isdir, mock_setup_logging
):
    mock_isdir.return_value = False

    args = MockArgs(
        repo_path="/nonexistent/repo",
        remote_url=None,
        remote_branch="main",
        output="/test/output.parquet",
        since=None,
        until=None,
        author=None,
        grep=None,
        merges=False,
        path=None,
        exclude_path=None,
        debug=False,
        verbose=False,
    )

    with pytest.raises(SystemExit):
        run_git_df_cli(args)

    mock_sys_exit.assert_called_once_with(1)
    mock_get_commits_df.assert_not_called()
    mock_write_table.assert_not_called()


@patch("git_dataframe_tools.cli.git_df.setup_logging")
@patch("git_dataframe_tools.cli.git_df.os.path.isdir")
@patch("git_dataframe_tools.cli.git_df.get_commits_df")
@patch("git_dataframe_tools.cli.git_df.pq.write_table")
def test_run_git_df_cli_empty_commits(
    mock_write_table, mock_get_commits_df, mock_isdir, mock_setup_logging
):
    mock_isdir.return_value = True
    mock_get_commits_df.return_value = pd.DataFrame()  # Empty DataFrame

    args = MockArgs(
        repo_path="/test/repo",
        remote_url=None,
        remote_branch="main",
        output="/test/output.parquet",
        since=None,
        until=None,
        author=None,
        grep=None,
        merges=False,
        path=None,
        exclude_path=None,
        debug=False,
        verbose=False,
    )

    run_git_df_cli(args)

    mock_setup_logging.assert_called_once_with(debug=False, verbose=False)
    mock_isdir.assert_called_once_with("/test/repo")
    mock_get_commits_df.assert_called_once()
    mock_write_table.assert_called_once()  # Should write an empty parquet file


@patch("git_dataframe_tools.cli.git_df.setup_logging")
@patch("git_dataframe_tools.cli.git_df.os.path.isdir")
@patch("git_dataframe_tools.cli.git_df.get_commits_df")
@patch("git_dataframe_tools.cli.git_df.pq.write_table")
@patch("git_dataframe_tools.cli.git_df.sys.exit", side_effect=SystemExit)
def test_run_git_df_cli_get_commits_df_exception(
    mock_sys_exit, mock_write_table, mock_get_commits_df, mock_isdir, mock_setup_logging
):
    mock_isdir.return_value = True
    mock_get_commits_df.side_effect = Exception("Test error")

    args = MockArgs(
        repo_path="/test/repo",
        remote_url=None,
        remote_branch="main",
        output="/test/output.parquet",
        since=None,
        until=None,
        author=None,
        grep=None,
        merges=False,
        path=None,
        exclude_path=None,
        debug=False,
        verbose=False,
    )

    with pytest.raises(SystemExit):
        run_git_df_cli(args)

    mock_sys_exit.assert_called_once_with(1)
    mock_write_table.assert_not_called()


@patch("git_dataframe_tools.cli.git_df.setup_logging")
@patch("git_dataframe_tools.cli.git_df.os.path.isdir")
@patch("git_dataframe_tools.cli.git_df.get_commits_df")
@patch("git_dataframe_tools.cli.git_df.pq.write_table")
def test_run_git_df_cli_remote_success(
    mock_write_table, mock_get_commits_df, mock_isdir, mock_setup_logging
):
    mock_get_commits_df.return_value = MOCKED_COMMITS_DF

    args = MockArgs(
        repo_path=".", # Default value, but remote_url takes precedence
        remote_url="https://github.com/test/remote_repo",
        remote_branch="dev",
        output="/test/remote_output.parquet",
        since=None,
        until=None,
        author=None,
        grep=None,
        merges=False,
        path=None,
        exclude_path=None,
        debug=False,
        verbose=False,
    )

    run_git_df_cli(args)

    mock_setup_logging.assert_called_once_with(debug=False, verbose=False)
    mock_isdir.assert_not_called() # os.path.isdir should not be called for remote repos
    mock_get_commits_df.assert_called_once_with(
        repo_path=None, # Should be None when remote_url is provided
        remote_url="https://github.com/test/remote_repo",
        remote_branch="dev",
        since=None,
        until=None,
        author=None,
        grep=None,
        merged_only=False,
        include_paths=None,
        exclude_paths=None,
    )
    mock_write_table.assert_called_once()