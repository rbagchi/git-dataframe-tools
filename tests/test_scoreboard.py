import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Assuming scoreboard.py is in the parent directory
from git_dataframe_tools.config_models import GitAnalysisConfig, _parse_period_string
from dateutil.relativedelta import relativedelta

# Import the main script to be tested
from git_dataframe_tools.cli import scoreboard

CONFIG_MODELS_MODULE_PATH = "git_dataframe_tools.config_models"
SCOREBOARD_MODULE_PATH = "git_dataframe_tools.cli.scoreboard"


# Test cases for _parse_period_string (already existing)
def test_parse_period_string_valid_days():
    assert _parse_period_string("1 day") == timedelta(days=1)
    assert _parse_period_string("5 days") == timedelta(days=5)


def test_parse_period_string_valid_weeks():
    assert _parse_period_string("1 week") == timedelta(weeks=1)
    assert _parse_period_string("2 weeks") == timedelta(weeks=2)


def test_parse_period_string_valid_months():
    assert _parse_period_string("1 month") == relativedelta(months=1)
    assert _parse_period_string("3 months") == relativedelta(months=3)


def test_parse_period_string_valid_years():
    assert _parse_period_string("1 year") == relativedelta(years=1)
    assert _parse_period_string("2 years") == relativedelta(years=2)


def test_parse_period_string_invalid_format():
    with pytest.raises(ValueError, match="Invalid period format"):
        _parse_period_string("abc")
    with pytest.raises(ValueError, match="Invalid period format"):
        _parse_period_string("3 lightyears")
    with pytest.raises(ValueError, match="Invalid period format"):
        _parse_period_string("month")


# Test cases for GitAnalysisConfig._get_date_range (already existing)
@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_default(mock_calendar_class, mock_datetime_class):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 29, 0, 0, 0), 1)  # for end_date if it's not provided
    ]

    config = GitAnalysisConfig()
    assert config.end_date.isoformat() == "2025-09-29"
    assert (
        config.start_date.isoformat() == "2025-06-29"
    )  # 3 months (relativedelta) before 2025-09-29 is 2025-06-29"


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_custom_start_end(mock_calendar_class, mock_datetime_class):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 3, 31, 0, 0, 0), 1),  # for end_date
        (datetime(2025, 1, 1, 0, 0, 0), 1),  # for start_date
    ]

    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-03-31")
    assert config.start_date.isoformat() == "2025-01-01"
    assert config.end_date.isoformat() == "2025-03-31"


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_natural_language_start_end(
    mock_calendar_class, mock_datetime_class
):
    mock_datetime_class.now.return_value = datetime(
        2025, 9, 29, 10, 0, 0
    )  # Add time for parsedatetime context
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 28, 0, 0, 0), 1),  # for "yesterday"
        (datetime(2025, 9, 22, 0, 0, 0), 1),  # for "last week"
    ]

    config = GitAnalysisConfig(start_date="last week", end_date="yesterday")
    assert config.start_date.isoformat() == "2025-09-22"
    assert config.end_date.isoformat() == "2025-09-28"


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_custom_default_period(mock_calendar_class, mock_datetime_class):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 29, 0, 0, 0), 1)  # for end_date if it's not provided
    ]

    config = GitAnalysisConfig(default_period="6 months")
    assert config.end_date.isoformat() == "2025-09-29"
    assert (
        config.start_date.isoformat() == "2025-03-29"
    )  # 6 months (relativedelta) before 2025-09-29 is 2025-03-29


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_invalid_start_date_format(
    mock_calendar_class, mock_datetime_class
):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.return_value = (None, 0)  # for invalid start_date

    with pytest.raises(ValueError, match="Could not parse start date: invalid-date"):
        GitAnalysisConfig(start_date="invalid-date")


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_invalid_end_date_format(
    mock_calendar_class, mock_datetime_class
):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.return_value = (None, 0)  # for invalid end_date

    with pytest.raises(ValueError, match="Could not parse end date: invalid-date"):
        GitAnalysisConfig(end_date="invalid-date")


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_start_after_end(mock_calendar_class, mock_datetime_class):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 28, 0, 0, 0), 1),  # for end_date
        (datetime(2025, 9, 29, 0, 0, 0), 1),  # for start_date
    ]

    with pytest.raises(ValueError, match="Start date cannot be after end date."):
        GitAnalysisConfig(start_date="2025-09-29", end_date="2025-09-28")


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
@patch(f"{CONFIG_MODELS_MODULE_PATH}._parse_period_string")
def test_get_date_range_invalid_default_period(
    mock_parse_period_string, mock_calendar_class, mock_datetime_class
):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min = MagicMock(
        time=MagicMock(return_value=datetime.min.time())
    )

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 29, 0, 0, 0), 1)  # for end_date if it's not provided
    ]

    mock_parse_period_string.side_effect = ValueError("Error parsing default period")

    with pytest.raises(ValueError, match="Error parsing default period"):
        GitAnalysisConfig(default_period="invalid period string")


# --- Tests for scoreboard.py ---


@patch.object(sys, "argv", ["scoreboard.py"])
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
    assert args.default_period == "3 months"
    assert args.df_path is None
    assert args.force_version_mismatch is False
    assert args.verbose is False
    assert args.debug is False


@patch.object(
    sys,
    "argv",
    [
        "scoreboard.py",
        "~/my_repo",
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
    assert args.repo_path == "~/my_repo"
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


@patch.object(sys, "argv", ["scoreboard.py", "-a", "test", "-m"])
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_author_and_me_mutually_exclusive(mock_logger):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "Error: Cannot use both --author and --me options together"
    )


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "data.parquet", "my_repo"])
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_df_path_with_custom_repo_path_mutually_exclusive(mock_logger):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "Error: Cannot use --df-path with a custom repo_path. The --df-path option replaces direct Git repository analysis."
    )


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "non_existent.parquet"])
@patch(f"{SCOREBOARD_MODULE_PATH}.os.path.exists", return_value=False)
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_df_path_not_found(mock_logger, mock_exists):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "DataFrame file not found at 'non_existent.parquet'"
    )


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "data.parquet"])
@patch(f"{SCOREBOARD_MODULE_PATH}.os.path.exists", return_value=True)
@patch(f"{SCOREBOARD_MODULE_PATH}.pq.read_table")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_df_path_read_error(mock_logger, mock_read_table, mock_exists):
    mock_read_table.side_effect = Exception("Parquet read error")
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "Error loading DataFrame from 'data.parquet': Parquet read error"
    )


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "data.parquet"])
@patch(f"{SCOREBOARD_MODULE_PATH}.os.path.exists", return_value=True)
@patch(f"{SCOREBOARD_MODULE_PATH}.pq.read_table")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_df_path_version_mismatch_abort(mock_logger, mock_read_table, mock_exists):
    mock_table = MagicMock()
    mock_table.schema.metadata = {b"data_version": b"2.0"}
    mock_read_table.return_value = mock_table
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "DataFrame version mismatch. Expected '1.0', but found '2.0'. Aborting. Use --force-version-mismatch to proceed anyway."
    )


@patch.object(
    sys,
    "argv",
    ["scoreboard.py", "--df-path", "data.parquet", "--force-version-mismatch"],
)
@patch(f"{SCOREBOARD_MODULE_PATH}.os.path.exists", return_value=True)
@patch(f"{SCOREBOARD_MODULE_PATH}.pq.read_table")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
@patch(f"{SCOREBOARD_MODULE_PATH}.setup_logging")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.get_ranking")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
@patch("datetime.datetime")
def test_main_df_path_version_mismatch_force(
    mock_datetime,
    mock_print,
    mock_print_header,
    mock_get_ranking,
    mock_parse_git_log,
    mock_setup_logging,
    mock_logger,
    mock_read_table,
    mock_exists,
):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.combine = datetime.combine
    mock_datetime.date = datetime.date
    mock_datetime.min = MagicMock(time=MagicMock(return_value=datetime.min.time()))
    mock_table = MagicMock()
    mock_table.schema.metadata = {b"data_version": b"2.0"}
    mock_table.to_pandas.return_value = pd.DataFrame()
    mock_read_table.return_value = mock_table
    mock_parse_git_log.return_value = {}
    mock_get_ranking.return_value = []

    assert scoreboard.main() == 1
    mock_logger.warning.assert_any_call(
        "DataFrame version mismatch. Expected '1.0', but found '2.0'. Proceeding due to --force-version-mismatch."
    )


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "data.parquet"])
@patch(f"{SCOREBOARD_MODULE_PATH}.os.path.exists", return_value=True)
@patch(f"{SCOREBOARD_MODULE_PATH}.pq.read_table")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.get_ranking")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
def test_main_df_path_no_version_metadata_abort(
    mock_print,
    mock_print_header,
    mock_get_ranking,
    mock_parse_git_log,
    mock_logger,
    mock_read_table,
    mock_exists,
):
    mock_table = MagicMock()
    mock_table.schema.metadata = {}  # No data_version metadata
    mock_read_table.return_value = mock_table
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "No 'data_version' metadata found in the DataFrame file. Aborting. Use --force-version-mismatch to proceed anyway."
    )


@patch.object(
    sys,
    "argv",
    ["scoreboard.py", "--df-path", "data.parquet", "--force-version-mismatch"],
)
@patch(f"{SCOREBOARD_MODULE_PATH}.os.path.exists", return_value=True)
@patch(f"{SCOREBOARD_MODULE_PATH}.pq.read_table")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
@patch(f"{SCOREBOARD_MODULE_PATH}.setup_logging")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.get_ranking")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
@patch("datetime.datetime")
def test_main_df_path_no_version_metadata_force(
    mock_datetime,
    mock_print,
    mock_print_header,
    mock_get_ranking,
    mock_parse_git_log,
    mock_setup_logging,
    mock_logger,
    mock_read_table,
    mock_exists,
):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.combine = datetime.combine
    mock_datetime.date = datetime.date
    mock_datetime.min = MagicMock(time=MagicMock(return_value=datetime.min.time()))
    mock_table = MagicMock()
    mock_table.schema.metadata = {}
    mock_table.to_pandas.return_value = pd.DataFrame()
    mock_read_table.return_value = mock_table
    mock_parse_git_log.return_value = {}
    mock_get_ranking.return_value = []

    assert scoreboard.main() == 1
    mock_logger.warning.assert_any_call(
        "No 'data_version' metadata found in the DataFrame file. Proceeding due to --force-version-mismatch."
    )


@patch.object(sys, "argv", ["scoreboard.py"])
@patch(
    f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=False
)
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_not_a_git_repo(mock_logger, mock_check_git_repo):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with("Not in a git repository")


@patch.object(sys, "argv", ["scoreboard.py"])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_get_commits_df_error(
    mock_logger, mock_get_commits_df, mock_check_git_repo
):
    mock_get_commits_df.side_effect = Exception("Git error")
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with("Error fetching git log data: Git error")


@patch.object(sys, "argv", ["scoreboard.py"])
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
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
    assert warning_call_args[0].startswith("No commits found in the specified time period")


@patch.object(sys, "argv", ["scoreboard.py", "-a", "John Doe"])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.find_author_stats")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_author_specific_no_match(
    mock_logger,
    mock_print,
    mock_print_header,
    mock_find_author_stats,
    mock_parse_git_log,
    mock_get_commits_df,
    mock_check_git_repo,
):
    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {}
    mock_find_author_stats.return_value = []

    assert scoreboard.main() == 1
    
    mock_logger.error.assert_called_with("No authors found matching 'John Doe'")
    mock_print.assert_any_call(
        "Suggestion: Try a partial match like first name, last name, or email domain."
    )


@patch.object(sys, "argv", ["scoreboard.py", "-a", "John Doe"])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.find_author_stats")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
def test_main_author_specific_single_match(
    mock_logger,
    mock_print,
    mock_print_header,
    mock_find_author_stats,
    mock_parse_git_log,
    mock_get_commits_df,
    mock_check_git_repo,
):
    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {}
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

    assert scoreboard.main() == 0
    mock_print_header.assert_any_call("Author Stats for 'John Doe' (commits)")
    mock_print.assert_any_call("  Rank:          #1 of 1 authors")
    mock_print.assert_any_call("  Lines Added:   100")
    mock_print.assert_any_call("  Lines Deleted: 50")
    mock_print.assert_any_call("  Total Diff:    150")
    mock_print.assert_any_call("  Commits:       10")
    mock_print.assert_any_call("  Diff Decile:   1 (1=top 10%, 10=bottom 10%)")
    mock_print.assert_any_call("  Commit Decile: 1 (1=top 10%, 10=bottom 10%)")
    mock_print.assert_any_call("  Percentile:    Top 0.0%")
    mock_print.assert_any_call("  Avg Diff/Commit: 15 lines")


@patch.object(sys, "argv", ["scoreboard.py"])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.get_ranking")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
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


@patch.object(sys, "argv", ["scoreboard.py", "-m"])
@patch(f"{SCOREBOARD_MODULE_PATH}.GitAnalysisConfig._check_git_repo", return_value=True)
@patch("git2df.get_commits_df")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.parse_git_log")
@patch(f"{SCOREBOARD_MODULE_PATH}.stats_module.find_author_stats")
@patch(f"{SCOREBOARD_MODULE_PATH}.print_header")
@patch(f"{SCOREBOARD_MODULE_PATH}.print")
@patch(f"{SCOREBOARD_MODULE_PATH}.logger")
@patch("git.Repo")
def test_main_me_option(
    mock_repo,
    mock_logger,
    mock_print,
    mock_print_header,
    mock_find_author_stats,
    mock_parse_git_log,
    mock_get_commits_df,
    mock_check_git_repo,
):
    mock_config_reader = MagicMock()
    mock_config_reader.get_value.side_effect = ["Current User", "current@example.com"]
    mock_repo.return_value.config_reader.return_value = mock_config_reader
    
    mock_get_commits_df.return_value = pd.DataFrame()
    mock_parse_git_log.return_value = {}
    mock_find_author_stats.return_value = [
        {
            "author_name": "Current User",
            "author_email": "current@example.com",
            "rank": 1,
            "added": 100,
            "deleted": 50,
            "total": 150,
            "commits": 10,
            "diff_decile": 1,
            "commit_decile": 1,
        }
    ]
    assert scoreboard.main() == 0
    mock_logger.info.assert_any_call(
        "Looking up stats for current user: Current User <current@example.com>"
    )
    mock_print_header.assert_any_call("Author Stats for 'Current User|current@example.com' (commits)")
    mock_print.assert_any_call("  Rank:          #1 of 1 authors")
