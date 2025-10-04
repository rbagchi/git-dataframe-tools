import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import pandas as pd

# Assuming scoreboard.py is in the parent directory
from git_dataframe_tools.config_models import GitAnalysisConfig, _parse_period_string
from dateutil.relativedelta import relativedelta

# Import the main script to be tested
from git_dataframe_tools.cli import scoreboard

CONFIG_MODELS_MODULE_PATH = "git_dataframe_tools.config_models"
SCOREBOARD_MODULE_PATH = "git_dataframe_tools.cli.scoreboard"


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
    mock_datetime_class.min.time.return_value = datetime.min.time()

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.return_value = (None, 0)  # for invalid start_date

    with pytest.raises(ValueError, match="Could not parse start date: invalid-date"):
        GitAnalysisConfig(_start_date_str="invalid-date")


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
    mock_datetime_class.min.time.return_value = datetime.min.time()

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.return_value = (None, 0)  # for invalid end_date

    with pytest.raises(ValueError, match="Could not parse end date: invalid-date"):
        GitAnalysisConfig(_end_date_str="invalid-date")


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "non_existent.parquet"])
@patch("git_dataframe_tools.cli._data_loader.os.path.exists", return_value=False)
@patch("git_dataframe_tools.cli._data_loader.logger")
def test_main_df_path_not_found(mock_logger, mock_exists):
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "DataFrame file not found at 'non_existent.parquet'"
    )


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "data.parquet"])
@patch("git_dataframe_tools.cli._data_loader.os.path.exists", return_value=True)
@patch("git_dataframe_tools.cli._data_loader.pq.read_table")
@patch("git_dataframe_tools.cli._data_loader.logger")
def test_main_df_path_read_error(mock_logger, mock_read_table, mock_exists):
    mock_read_table.side_effect = Exception("Parquet read error")
    assert scoreboard.main() == 1
    mock_logger.error.assert_called_with(
        "Error loading DataFrame from 'data.parquet': Parquet read error"
    )


@patch.object(sys, "argv", ["scoreboard.py", "--df-path", "data.parquet"])
@patch("git_dataframe_tools.cli._data_loader.os.path.exists", return_value=True)
@patch("git_dataframe_tools.cli._data_loader.pq.read_table")
@patch("git_dataframe_tools.cli._data_loader.logger")
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
@patch("git_dataframe_tools.cli._data_loader.os.path.exists", return_value=True)
@patch("git_dataframe_tools.cli._data_loader.pq.read_table")
@patch("git2df.get_commits_df")
@patch("git_dataframe_tools.cli._data_loader.logger")
@patch("datetime.datetime")
@patch("git_dataframe_tools.git_stats_pandas.parse_git_log")
@patch("git_dataframe_tools.git_stats_pandas.get_ranking")
def test_main_df_path_version_mismatch_force(
    mock_get_ranking,
    mock_parse_git_log,
    mock_datetime,
    mock_logger,
    mock_get_commits_df,
    mock_read_table,
    mock_exists,
):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.combine = datetime.combine
    mock_datetime.date = datetime.date
    mock_datetime.min.time.return_value = datetime.min.time()
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
@patch("git_dataframe_tools.cli._data_loader.os.path.exists", return_value=True)
@patch("git_dataframe_tools.cli._data_loader.pq.read_table")
@patch("git_dataframe_tools.cli._data_loader.logger")
@patch("git_dataframe_tools.git_stats_pandas.parse_git_log")
@patch("git_dataframe_tools.git_stats_pandas.get_ranking")
@patch("git_dataframe_tools.cli._display_utils.print_header")
@patch("builtins.print")
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
@patch("git_dataframe_tools.cli._data_loader.os.path.exists", return_value=True)
@patch("git_dataframe_tools.cli._data_loader.pq.read_table")
@patch("git_dataframe_tools.cli._data_loader.logger")
@patch("git_dataframe_tools.cli.scoreboard.setup_logging")
@patch("git_dataframe_tools.git_stats_pandas.parse_git_log")
@patch("git_dataframe_tools.git_stats_pandas.get_ranking")
@patch("git_dataframe_tools.cli._display_utils.print_header")
@patch("builtins.print")
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
    mock_datetime.min.time.return_value = datetime.min.time()
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
