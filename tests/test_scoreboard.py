import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import sys

# Assuming scoreboard.py is in the parent directory

from git_scoreboard.scoreboard import GitAnalysisConfig
from git_scoreboard.git_stats import _parse_period_string
from dateutil.relativedelta import relativedelta

SCOREBOARD_MODULE_PATH = "git_scoreboard.scoreboard"

SCOREBOARD_MODULE_PATH = "git_scoreboard.scoreboard"


# Test cases for _parse_period_string
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


# Test cases for GitAnalysisConfig._get_date_range
# Mock datetime.now() to ensure consistent test results
@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_default(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.strptime = datetime.strptime  # Keep original strptime
    mock_datetime.timedelta = timedelta  # Keep original timedelta

    config = GitAnalysisConfig()
    start_date_str, end_date_str = config._get_date_range()
    assert end_date_str == "2025-09-29"
    assert (
        start_date_str == "2025-06-29"
    )  # 3 months (relativedelta) before 2025-09-29 is 2025-06-29


@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_custom_start_end(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    config = GitAnalysisConfig(start_date="2025-01-01", end_date="2025-03-31")
    start_date_str, end_date_str = config._get_date_range()
    assert start_date_str == "2025-01-01"
    assert end_date_str == "2025-03-31"


@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_natural_language_start_end(mock_datetime):
    mock_datetime.now.return_value = datetime(
        2025, 9, 29, 10, 0, 0
    )  # Add time for parsedatetime context
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    config = GitAnalysisConfig(start_date="last week", end_date="yesterday")
    start_date_str, end_date_str = config._get_date_range()
    # Assuming 'last week' from 2025-09-29 is 2025-09-22
    # Assuming 'yesterday' from 2025-09-29 is 2025-09-28
    assert start_date_str == "2025-09-22"
    assert end_date_str == "2025-09-28"


@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_custom_default_period(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    config = GitAnalysisConfig(default_period="6 months")
    start_date_str, end_date_str = config._get_date_range()
    assert end_date_str == "2025-09-29"
    assert (
        start_date_str == "2025-03-29"
    )  # 6 months (relativedelta) before 2025-09-29 is 2025-03-29


@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_invalid_start_date_format(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    with pytest.raises(ValueError, match="Invalid start date format"):
        GitAnalysisConfig(start_date="invalid-date")


@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_invalid_end_date_format(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    with pytest.raises(ValueError, match="Invalid end date format"):
        GitAnalysisConfig(end_date="invalid-date")


@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_start_after_end(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    with pytest.raises(ValueError, match="Start date must be before end date."):
        GitAnalysisConfig(start_date="2025-09-29", end_date="2025-09-28")


@patch(f"{SCOREBOARD_MODULE_PATH}.datetime")
def test_get_date_range_invalid_default_period(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    with pytest.raises(ValueError, match="Error parsing default period"):
        GitAnalysisConfig(default_period="invalid period string")
