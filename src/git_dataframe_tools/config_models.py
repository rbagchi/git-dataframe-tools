import sys
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional, Union
from parsedatetime import Calendar, parsedatetime
from dateutil.relativedelta import relativedelta
import re
from enum import Enum

from git_dataframe_tools.git_repo_info_provider import GitRepoInfoProvider


class OutputFormat(str, Enum):
    TABLE = "table"
    MARKDOWN = "markdown"


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    BOLD = "\033[1m"
    NC = "\033[0m"  # No Color


def print_colored(text, color):
    """Print colored text"""
    if sys.stdout.isatty():
        print(f"{color}{text}{Colors.NC}")
    else:
        print(text)


def print_header(text):
    print_colored(text, Colors.BOLD + Colors.BLUE)


def print_success(text):
    print_colored(text, Colors.GREEN)


def print_warning(text):
    print_colored(text, Colors.YELLOW)


def print_error(text):
    print_colored(text, Colors.RED)


def _parse_period_string(period_str: str) -> Union[timedelta, relativedelta]:
    """Parses a period string like '3 months' or '1 year' into a timedelta."""
    period_str = period_str.lower().strip()
    match = re.match(r"^(\d+)\s+(day|week|month|year)s?(\s+ago)?$", period_str)
    if not match:
        raise ValueError(
            f"Invalid period format: {period_str}. Use format like '3 months' or '1 year'."
        )

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "day":
        return timedelta(days=value)
    elif unit == "week":
        return timedelta(weeks=value)
    elif unit == "month":
        return relativedelta(months=value)
    elif unit == "year":
        return relativedelta(years=value)
    else:
        # Should not happen due to regex, but for safety
        raise ValueError(f"Unknown unit: {unit}")


@dataclass
class GitAnalysisConfig:
    """Configuration object for git analysis parameters"""

    _start_date_str: Optional[str] = None
    _end_date_str: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    author_query: Optional[str] = None
    use_current_user: bool = False
    merged_only: bool = False
    include_paths: Optional[list[str]] = None
    exclude_paths: Optional[list[str]] = None
    default_period: Optional[str] = None
    current_user_name: Optional[str] = None
    current_user_email: Optional[str] = None
    repo_info_provider: Optional[GitRepoInfoProvider] = field(compare=False, default=None)

    def __post_init__(self):
        self._set_date_range()
        if self.use_current_user:
            self._set_current_git_user()
        if self.author_query is None and self.use_current_user:
            self.author_query = f"{self.current_user_name}|{self.current_user_email}"

    def _set_date_range(self):
        cal = Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        original_end_date_str = self._end_date_str
        original_start_date_str = self._start_date_str

        if original_end_date_str:
            parsed_end_date, parse_status = cal.parseDT(original_end_date_str)
            if not parse_status:
                raise ValueError(f"Could not parse end date: {original_end_date_str}")
            self.end_date = parsed_end_date.date()
        else:
            self.end_date = today.date()

        if original_start_date_str:
            parsed_start_date, parse_status = cal.parseDT(original_start_date_str)
            if not parse_status:
                raise ValueError(
                    f"Could not parse start date: {original_start_date_str}"
                )
            self.start_date = parsed_start_date.date()
        else:
            # Default period if no start date is specified
            period_str = self.default_period if self.default_period else "3 months"
            period = _parse_period_string(period_str)
            self.start_date = (
                datetime.combine(self.end_date, datetime.min.time()) - period
            ).date()

        if self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date.")

    def _set_current_git_user(self):
        if self.use_current_user and self.repo_info_provider is None:
            print_error("Error: GitRepoInfoProvider must be provided when use_current_user is True.")
            sys.exit(1)
        if not self.repo_info_provider.is_git_repo(os.getcwd()):
            print_error("Error: Not in a git repository")
            sys.exit(1)
        try:
            self.current_user_name, self.current_user_email = self.repo_info_provider.get_current_user_info(
                os.getcwd()
            )
        except Exception as e:
            print_error(
                f"Error: Could not retrieve git user.name or user.email: {e}. Please configure git or run without --me."
            )
            sys.exit(1)

    def is_author_specific(self) -> bool:
        """Checks if the analysis is focused on a specific author."""
        return self.author_query is not None

    def get_analysis_description(self) -> str:
        """Returns a description of the current analysis configuration."""
        start_date_str = self.start_date.isoformat() if self.start_date else "N/A"
        end_date_str = self.end_date.isoformat() if self.end_date else "N/A"
        desc = f"Analysis period: {start_date_str} to {end_date_str}"
        if self.merged_only:
            desc += ", merged commits only"
        if self.include_paths:
            desc += f", paths: {', '.join(self.include_paths)}"
        if self.exclude_paths:
            desc += f", excluding paths: {', '.join(self.exclude_paths)}"
        return desc
