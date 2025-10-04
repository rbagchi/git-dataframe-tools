import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from dateutil.relativedelta import relativedelta

from git_dataframe_tools.config_models import GitAnalysisConfig, _parse_period_string

CONFIG_MODELS_MODULE_PATH = "git_dataframe_tools.config_models"


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_default(mock_calendar_class, mock_datetime_class):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min.time.return_value = datetime.min.time()

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 29, 0, 0, 0), 1)  # for end_date if it's not provided
    ]

    config = GitAnalysisConfig()
    assert config.end_date.isoformat() == "2025-09-29"
    assert (
        config.start_date.isoformat() == "2025-06-29"  # 3 months (relativedelta) before 2025-09-29 is 2025-06-29"
    )


@patch(f"{CONFIG_MODELS_MODULE_PATH}.datetime")
@patch(f"{CONFIG_MODELS_MODULE_PATH}.Calendar")
def test_get_date_range_custom_start_end(mock_calendar_class, mock_datetime_class):
    mock_datetime_class.now.return_value = datetime(2025, 9, 29)
    mock_datetime_class.strptime = datetime.strptime
    mock_datetime_class.timedelta = timedelta
    mock_datetime_class.combine = datetime.combine
    mock_datetime_class.date = datetime.date
    mock_datetime_class.min.time.return_value = datetime.min.time()

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 3, 31, 0, 0, 0), 1),  # for end_date
        (datetime(2025, 1, 1, 0, 0, 0), 1),  # for start_date
    ]

    config = GitAnalysisConfig(_start_date_str="2025-01-01", _end_date_str="2025-03-31")
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
    mock_datetime_class.min.time.return_value = datetime.min.time()

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 28, 0, 0, 0), 1),  # for "yesterday"
        (datetime(2025, 9, 22, 0, 0, 0), 1),  # for "last week"
    ]

    config = GitAnalysisConfig(_start_date_str="last week", _end_date_str="yesterday")
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
    mock_datetime_class.min.time.return_value = datetime.min.time()

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

    config = GitAnalysisConfig(default_period="6 months")
    assert config.end_date.isoformat() == "2025-09-29"
    assert (
        config.start_date.isoformat() == "2025-03-29"
    )  # 6 months (relativedelta) before 2025-09-29 is 2025-03-29


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
    mock_datetime_class.min.time.return_value = datetime.min.time()

    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 29, 0, 0, 0), 1)  # for end_date if it's not provided
    ]

    mock_parse_period_string.side_effect = ValueError("Error parsing default period")

    with pytest.raises(ValueError, match="Error parsing default period"):
        GitAnalysisConfig(default_period="invalid period string")
