import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import sys

# Assuming scoreboard.py is in the parent directory

from git_scoreboard.scoreboard import GitAnalysisConfig

@patch('git_scoreboard.scoreboard.datetime')
def test_get_date_range_natural_language_start_end(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 9, 29, 10, 0, 0) # Add time for parsedatetime context
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta

    config = GitAnalysisConfig(start_date="last week", end_date="yesterday")
    start_date_str, end_date_str = config._get_date_range()
    # Assuming 'last week' from 2025-09-29 is 2025-09-22
    # Assuming 'yesterday' from 2025-09-29 is 2025-09-28
    assert start_date_str == "2025-09-22"
    assert end_date_str == "2025-09-28"
