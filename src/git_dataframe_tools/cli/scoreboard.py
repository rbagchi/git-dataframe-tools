#!/usr/bin/env python3
"""
Git Author Ranking by Diff Size (Last 3 Months)
This script analyzes git history and ranks authors by total lines changed
"""

__version__ = "0.1.0"

import argparse
import logging
import sys

from git_dataframe_tools.config_models import (
    GitAnalysisConfig,
)
import git_dataframe_tools.git_stats_pandas as stats_module
from git_dataframe_tools.logger import setup_logging

from git_dataframe_tools.cli._validation import _validate_arguments
from git_dataframe_tools.cli._data_loader import _load_dataframe, _gather_git_data
from git_dataframe_tools.cli._display_utils import (
    _display_author_specific_stats,
    _display_full_ranking,
)

EXPECTED_DATA_VERSION = "1.0"  # Expected major version of the DataFrame schema

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Git Author Ranking by Diff Size (Last 3 Months)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the Git repository (default: current directory).",
    )
    parser.add_argument(
        "-S",
        "--since",
        help='Start date for analysis (e.g., "2023-01-01", "3 months ago", "1 year ago")',
    )
    parser.add_argument(
        "-U", "--until", help='End date for analysis (e.g., "2023-03-31", "now")'
    )
    parser.add_argument(
        "-a",
        "--author",
        help='Filter by author name or email (e.g., "John Doe", "john@example.com")',
    )
    parser.add_argument(
        "-m",
        "--me",
        action="store_true",
        help="Filter by current git user (uses git config user.name and user.email)",
    )
    parser.add_argument(
        "--merges",
        action="store_true",
        help="Only include commits that are merged into the current branch (e.g., via pull requests)",
    )
    parser.add_argument(
        "-p",
        "--path",
        action="append",
        help="Include only changes in specified paths (can be used multiple times)",
    )
    parser.add_argument(
        "-x",
        "--exclude-path",
        action="append",
        help="Exclude changes in specified paths (can be used multiple times)",
    )
    parser.add_argument(
        "--default-period",
        default="3 months",
        help='Default period if --since or --until are not specified (e.g., "3 months", "1 year")',
    )

    parser.add_argument(
        "--df-path",
        help="Path to a Parquet file containing pre-extracted Git commit data (e.g., from git-df).",
    )
    parser.add_argument(
        "--force-version-mismatch",
        action="store_true",
        help="Proceed with analysis even if the DataFrame version does not match the expected version.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (INFO level)",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug output (DEBUG level)"
    )

    return parser.parse_args()


def main():
    """Main function"""
    args = parse_arguments()
    setup_logging(debug=args.debug, verbose=args.verbose)
    logger.debug(f"CLI arguments: {args}")

    validation_result = _validate_arguments(args)
    if validation_result != 0:
        return validation_result

    # Create configuration object
    config = GitAnalysisConfig(
        start_date=args.since,
        end_date=args.until,
        author_query=args.author,
        use_current_user=args.me,
        merged_only=args.merges,
        include_paths=args.path,
        exclude_paths=args.exclude_path,
        default_period=args.default_period,
    )

    git_log_data, status_code = _load_dataframe(args, config)
    if status_code != 0:
        return status_code

    if git_log_data is None:
        git_log_data, status_code = _gather_git_data(args, config)
        if status_code != 0:
            return status_code

    logger.info("Processing commits...")
    parsed_git_log_data = stats_module.parse_git_log(git_log_data)

    # If author-specific analysis requested, show only their stats
    if config.is_author_specific():
        author_stats_list = stats_module.find_author_stats(
            parsed_git_log_data, config.author_query
        )
        return _display_author_specific_stats(config, author_stats_list)
    else:
        # Otherwise show full ranking
        # When not author-specific, find_author_stats should return all authors
        all_author_stats_list = stats_module.find_author_stats(
            parsed_git_log_data, None
        )
        author_list = stats_module.get_ranking(all_author_stats_list)
        return _display_full_ranking(config, author_list)


def cli():
    sys.exit(main())


if __name__ == "__main__":
    cli()
