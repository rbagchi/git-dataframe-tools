import pytest
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from git_dataframe_tools.config_models import _parse_period_string


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

def test_parse_period_string_with_articles():
    assert _parse_period_string("a day") == timedelta(days=1)
    assert _parse_period_string("a week") == timedelta(weeks=1)
    assert _parse_period_string("a month") == relativedelta(months=1)
    assert _parse_period_string("a year") == relativedelta(years=1)
