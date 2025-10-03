from datetime import datetime
from unittest.mock import patch, MagicMock

# Assuming scoreboard.py is in the parent directory

from git_scoreboard.config_models import GitAnalysisConfig

CONFIG_MODELS_MODULE_PATH = "git_scoreboard.config_models"

@patch(f'{CONFIG_MODELS_MODULE_PATH}.datetime')
@patch(f'{CONFIG_MODELS_MODULE_PATH}.Calendar')
def test_get_date_range_natural_language_start_end(mock_calendar_class, mock_datetime_class):
    # Mock datetime.now() to control the 'today' reference
    mock_datetime_class.now.return_value = datetime(2025, 9, 29, 10, 0, 0) # Monday, Sep 29, 2025
    mock_datetime_class.combine = datetime.combine

    # Mock the Calendar instance and its parseDT method
    mock_cal_instance = MagicMock()
    mock_calendar_class.return_value = mock_cal_instance
    # Configure side_effect for parseDT calls
    # First call for 'yesterday' (relative to 2025-09-29) -> 2025-09-28
    # Second call for 'last week' (relative to 2025-09-29) -> 2025-09-22
    mock_cal_instance.parseDT.side_effect = [
        (datetime(2025, 9, 28, 0, 0, 0), 1),  # for "yesterday"
        (datetime(2025, 9, 22, 0, 0, 0), 1)   # for "last week"
    ]

    config = GitAnalysisConfig(start_date="last week", end_date="yesterday")
    assert config.start_date.isoformat() == "2025-09-22"
    assert config.end_date.isoformat() == "2025-09-28"
