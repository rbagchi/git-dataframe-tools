from unittest.mock import patch, MagicMock
import sys
import pandas as pd

# Assuming scoreboard.py is in the parent directory

# Import the main script to be tested
from git_dataframe_tools.cli import scoreboard

CONFIG_MODELS_MODULE_PATH = "git_dataframe_tools.config_models"
SCOREBOARD_MODULE_PATH = "git_dataframe_tools.cli.scoreboard"


# --- Tests for scoreboard.py ---


@patch.object(sys, "argv", ["scoreboard.py", "."])
def test_parse_arguments_default():
    args = scoreboard.parse_arguments()
    assert args.repo_path == "."
    assert args.since is None
    assert args.until is None
    assert args.author is None
    assert args.me is False
    assert args.merges is False
    assert args.path is None
    assert args.exclude_path is None
    assert args.default_period == "3 months ago"
    assert args.df_path is None
    assert args.force_version_mismatch is False
    assert args.verbose is False
    assert args.debug is False


@patch.object(
    sys,
    "argv",
    [
        "scoreboard.py",
        "--since",
        "2024-01-01",
        "-U",
        "2024-03-31",
        "-a",
        "John Doe",
        "--me",
        "--merges",
        "-p",
        "src",
        "-p",
        "docs",
        "-x",
        "tests",
        "--default-period",
        "6 months",
        "--df-path",
        "data.parquet",
        "--force-version-mismatch",
        "-v",
        "-d",
    ],
)
def test_parse_arguments_all_options():
    args = scoreboard.parse_arguments()
    assert args.repo_path == "."
    assert args.since == "2024-01-01"
    assert args.until == "2024-03-31"
    assert args.author == "John Doe"
    assert args.me is True
    assert args.merges is True
    assert args.path == ["src", "docs"]
    assert args.exclude_path == ["tests"]
    assert args.default_period == "6 months"
    assert args.df_path == "data.parquet"
    assert args.force_version_mismatch is True
    assert args.verbose is True
    assert args.debug is True


@patch.object(sys, "argv", ["scoreboard.py", ".", "--author", "test", "--me"])
@patch("git_dataframe_tools.cli._validation.logger")
def test_main_author_and_me_mutually_exclusive(mock_logger):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "Error: Cannot use both --author and --me options together"
    )





@patch.object(sys, "argv", ["scoreboard.py", "/tmp/non-existent-repo"])
@patch(
    f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=False
)
@patch("git_dataframe_tools.cli._data_loader.logger")
def test_main_not_a_git_repo(mock_logger, mock_check_git_repo):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with("Not in a git repository")


@patch.object(sys, "argv", ["scoreboard.py", "."])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch("git_dataframe_tools.cli._data_loader.logger")
def test_main_get_commits_df_error(
    mock_logger, mock_get_commits_df, mock_check_git_repo
):
    mock_get_commits_df.side_effect = Exception("Git error")
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with("Error fetching git log data: Git error")


@patch.object(sys, "argv", ["scoreboard.py", "."])
@patch("git_dataframe_tools.cli._display_utils.logger")
@patch("builtins.print")
@patch("git_dataframe_tools.cli._display_utils.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.get_ranking")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch("git2df.get_commits_df")
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
def test_main_no_commits_found(
    mock_check_git_repo,
    mock_get_commits_df,
    mock_parse_git_log,
    mock_get_ranking,
    mock_print_header,
    mock_print,
    mock_logger,
):
    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {}
    mock_get_ranking.return_value = []

    assert scoreboard.main() == 1

    # Get the call arguments from the mock
    warning_call_args = mock_logger.warning.call_args[0]

    # Check that the warning message starts with the expected string
    assert warning_call_args[0].startswith(
        "No commits found in the specified time period"
    )


@patch.object(sys, "argv", ["scoreboard.py", ".", "-a", "John Doe"])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch("git_dataframe_tools.git_stats_pandas.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}._display_author_specific_stats")
def test_main_author_specific_no_match(
    mock_display_author_specific_stats,
    mock_parse_git_log,
    mock_get_commits_df,
    mock_check_git_repo,
):
    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {}
    mock_display_author_specific_stats.return_value = 1

    assert scoreboard.main() == 1
    mock_display_author_specific_stats.assert_called_once()


@patch.object(sys, "argv", ["scoreboard.py", ".", "-a", "John Doe"])
@patch("git_dataframe_tools.git_stats_pandas.find_author_stats")
@patch("git_dataframe_tools.git_stats_pandas.parse_git_log")
@patch("git2df.get_commits_df")
@patch(f"{SCOREBOARD_MODULE_PATH}._display_author_specific_stats")
def test_main_author_specific_single_match(
    mock_display_author_specific_stats,
    mock_get_commits_df,
    mock_parse_git_log,
    mock_find_author_stats,
):
    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {
        "John Doe <john@example.com>": [
            {
                "author_name": "John Doe",
                "author_email": "john@example.com",
                "added": 10,
                "deleted": 5,
                "commit_hash": "abc",
            }
        ]
    }
    mock_find_author_stats.return_value = [
        {
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "rank": 1,
            "added": 100,
            "deleted": 50,
            "total": 150,
            "commits": 10,
            "diff_decile": 1,
            "commit_decile": 1,
        }
    ]
    mock_display_author_specific_stats.return_value = 0

    assert scoreboard.main() == 0
    mock_display_author_specific_stats.assert_called_once()


@patch.object(sys, "argv", ["scoreboard.py", "."])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch("git_dataframe_tools.git_stats_pandas.parse_git_log")
@patch("git_dataframe_tools.git_stats_pandas.get_ranking")
@patch("git_dataframe_tools.cli._display_utils.print_header")
@patch("builtins.print")
@patch("git_dataframe_tools.cli._display_utils.logger")
def test_main_full_ranking_output(
    mock_logger,
    mock_print,
    mock_print_header,
    mock_get_ranking,
    mock_parse_git_log,
    mock_get_commits_df,
    mock_check_git_repo,
):
    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {}
    mock_get_ranking.return_value = [
        {
            "author_name": "Author One",
            "author_email": "one@example.com",
            "rank": 1,
            "added": 200,
            "deleted": 100,
            "total": 300,
            "commits": 20,
            "diff_decile": 1,
            "commit_decile": 1,
        },
        {
            "author_name": "Author Two",
            "author_email": "two@example.com",
            "rank": 2,
            "added": 50,
            "deleted": 20,
            "total": 70,
            "commits": 5,
            "diff_decile": 5,
            "commit_decile": 5,
        },
    ]

    assert scoreboard.main() == 0
    mock_print_header.assert_any_call("Git Author Ranking by Diff Size")
    mock_print.assert_any_call(
        "   1 Author One <one@example.com>                          200          100         300      20      1      1"
    )
    mock_print.assert_any_call(
        "   2 Author Two <two@example.com>                           50           20          70       5      5      5"
    )
    mock_print.assert_any_call("\nDiff Size Decile Distribution:")
    mock_print.assert_any_call("     1                       300        1")
    mock_print.assert_any_call("     5                        70        1")
    mock_print.assert_any_call("\nCommit Count Decile Distribution:")
    mock_print.assert_any_call("     1              20        1")
    mock_print.assert_any_call("     5               5        1")
    mock_print.assert_any_call("- Total unique authors: 2")


@patch.object(sys, "argv", ["scoreboard.py", ".", "--me"])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch("git_dataframe_tools.git_stats_pandas.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}._display_author_specific_stats")
@patch("git.Repo")
def test_main_me_option(
    mock_repo,
    mock_display_author_specific_stats,
    mock_parse_git_log,
    mock_get_commits_df,
    mock_check_git_repo,
):
    mock_config_reader = MagicMock()
    mock_config_reader.get_value.side_effect = ["Current User", "current@example.com"]
    mock_repo.return_value.config_reader.return_value = mock_config_reader

    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {}
    mock_display_author_specific_stats.return_value = 0

    assert scoreboard.main() == 0
    mock_display_author_specific_stats.assert_called_once()
