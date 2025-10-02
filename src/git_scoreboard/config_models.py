import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from parsedatetime import Calendar, parsedatetime
from dateutil.relativedelta import relativedelta
import re

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def print_colored(text, color):
    """Print colored text"""
    print(f"{color}{text}{Colors.NC}")

def print_header(text):
    print_colored(text, Colors.BOLD + Colors.BLUE)

def print_success(text):
    print_colored(text, Colors.GREEN)

def print_warning(text):
    print_colored(text, Colors.YELLOW)

def print_error(text):
    print_colored(text, Colors.RED)

def _parse_period_string(period_str: str) -> timedelta:
    """Parses a period string like '3 months' or '1 year' into a timedelta."""
    period_str = period_str.lower().strip()
    match = re.match(r'^(\d+)\s*(day|week|month|year)s?$', period_str)
    if not match:
        raise ValueError(f"Invalid period format: {period_str}. Use format like '3 months' or '1 year'.")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == 'day':
        return timedelta(days=value)
    elif unit == 'week':
        return timedelta(weeks=value)
    elif unit == 'month':
        return relativedelta(months=value)
    elif unit == 'year':
        return relativedelta(years=value)
    else:
        # Should not happen due to regex, but for safety
        raise ValueError(f"Unknown unit: {unit}")

@dataclass
class GitAnalysisConfig:
    """Configuration object for git analysis parameters"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    author_query: Optional[str] = None
    use_current_user: bool = False
    merged_only: bool = False
    include_paths: Optional[list[str]] = None
    exclude_paths: Optional[list[str]] = None
    default_period: Optional[str] = None
    current_user_name: Optional[str] = None
    current_user_email: Optional[str] = None

    def __post_init__(self):
        self._set_date_range()
        if self.use_current_user:
            self._set_current_git_user()
        if self.author_query is None and self.use_current_user:
            self.author_query = f"{self.current_user_name}|{self.current_user_email}"

    def _set_date_range(self):
        cal = Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        original_end_date_str = self.end_date
        original_start_date_str = self.start_date

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
                raise ValueError(f"Could not parse start date: {original_start_date_str}")
            self.start_date = parsed_start_date.date()
        else:
            # Default period if no start date is specified
            period_str = self.default_period if self.default_period else "3 months"
            period = _parse_period_string(period_str)
            self.start_date = (datetime.combine(self.end_date, datetime.min.time()) - period).date()

        if self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date.")

    def _set_current_git_user(self):
        if not self._check_git_repo():
            print_error("Error: Not in a git repository")
            sys.exit(1)
        try:
            name_cmd = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True, check=True)
            email_cmd = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True, check=True)
            self.current_user_name = name_cmd.stdout.strip()
            self.current_user_email = email_cmd.stdout.strip()
        except subprocess.CalledProcessError:
            print_error("Error: Could not retrieve git user.name or user.email. Please configure git or run without --me.")
            sys.exit(1)

    def _check_git_repo(self):
        """Check if we're in a git repository"""
        try:
            subprocess.run(['git', 'rev-parse', '--git-dir'], 
                          capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_git_log_data(self) -> list[str]:
        """Fetches git log data based on the configuration."""
        git_log_cmd = [
            'git', 'log',
            f'--since={self.start_date.isoformat()}',
            f'--until={self.end_date.isoformat()}',
            '--numstat',
            '--pretty=format:--%H--%an--%ae--%ad--%s',
            '--date=iso'
        ]

        if self.merged_only:
            # Find the default branch (master or main)
            try:
                # Check for 'main' branch
                subprocess.run(['git', 'show-ref', '--verify', 'refs/heads/main'], check=True, capture_output=True)
                default_branch = 'main'
            except subprocess.CalledProcessError:
                try:
                    # Fallback to 'master' branch
                    subprocess.run(['git', 'show-ref', '--verify', 'refs/heads/master'], check=True, capture_output=True)
                    default_branch = 'master'
                except subprocess.CalledProcessError:
                    print_warning("Neither 'main' nor 'master' branch found. '--merged-only' might not work as expected.")
                    default_branch = 'main' # Default to main even if not found, git will handle the error if it doesn't exist

            git_log_cmd.extend([f'--merges', f'origin/{default_branch}'])

        if self.include_paths:
            git_log_cmd.extend(['--'] + self.include_paths)
        if self.exclude_paths:
            for p in self.exclude_paths:
                git_log_cmd.extend([f':(exclude){p}'])

        try:
            process = subprocess.run(git_log_cmd, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            return process.stdout.strip().splitlines()
        except subprocess.CalledProcessError as e:
            print_error(f"Error running git log: {e}")
            print_error(f"Stderr: {e.stderr}")
            sys.exit(1)
        except FileNotFoundError:
            print_error("Error: 'git' command not found. Please ensure Git is installed and in your PATH.")
            sys.exit(1)

    def is_author_specific(self) -> bool:
        """Checks if the analysis is focused on a specific author."""
        return self.author_query is not None

    def get_analysis_description(self) -> str:
        """Returns a description of the current analysis configuration."""
        desc = f"Analysis period: {self.start_date.isoformat()} to {self.end_date.isoformat()}"
        if self.merged_only:
            desc += ", merged commits only"
        if self.include_paths:
            desc += f", paths: {', '.join(self.include_paths)}"
        if self.exclude_paths:
            desc += f", excluding paths: {', '.join(self.exclude_paths)}"
        return desc
