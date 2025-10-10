#!/usr/bin/env python3
"""
Git Author Ranking by Diff Size (Last 3 Months)
This script analyzes git history and ranks authors by total lines changed
"""

__version__ = "0.1.0"

import typer
from typing import Optional, List
from typing_extensions import Annotated
import logging
import sys

from git_dataframe_tools.config_models import (
    GitAnalysisConfig,
)
import git_dataframe_tools.git_stats_pandas as stats_module
from git_dataframe_tools.logger import setup_logging

from git_dataframe_tools.cli._data_loader import _load_dataframe, _gather_git_data
from git_dataframe_tools.cli._display_utils import (
    _display_author_specific_stats,
    _display_full_ranking,
)

EXPECTED_DATA_VERSION = "1.0"  # Expected major version of the DataFrame schema

logger = logging.getLogger(__name__)

app = typer.Typer(help="Git Author Ranking by Diff Size (Last 3 Months)")


@app.command()
def main(
    repo_path: Annotated[
        Optional[str],
        typer.Argument(
            help="Path to the Git repository (default: current directory). Cannot be used with --remote-url or --df-path.",
        ),
    ] = ".",
    remote_url: Annotated[
        Optional[str],
        typer.Option(
            "--remote-url",
            help="URL of the remote Git repository to analyze (e.g., https://github.com/user/repo). Cannot be used with repo_path or --df-path.",
        ),
    ] = None,
    df_path: Annotated[
        Optional[str],
        typer.Option(
            "--df-path",
            help="Path to a Parquet file containing pre-extracted Git commit data (e.g., from git-df). Cannot be used with repo_path or --remote-url.",
        ),
    ] = None,
    remote_branch: Annotated[
        str,
        typer.Option(
            "--remote-branch",
            help="Branch of the remote repository to analyze (default: main). Only applicable with --remote-url.",
        ),
    ] = "main",
    since: Annotated[
        Optional[str],
        typer.Option(
            "-S",
            "--since",
            help='Start date for analysis (e.g., "2023-01-01", "3 months ago", "1 year ago")',
        ),
    ] = None,
    until: Annotated[
        Optional[str],
        typer.Option(
            "-U", "--until", help='End date for analysis (e.g., "2023-03-31", "now")'
        ),
    ] = None,
    author: Annotated[
        Optional[str],
        typer.Option(
            "-a",
            "--author",
            help='Filter by author name or email (e.g., "John Doe", "john@example.com")',
        ),
    ] = None,
    me: Annotated[
        bool,
        typer.Option("--me", help="Filter by your own git user name and email"),
    ] = False,
    merges: Annotated[
        bool,
        typer.Option(
            "-m",
            "--merges",
            help="Only include commits that are merged into the current branch (e.g., via pull requests)",
        ),
    ] = False,
    path: Annotated[
        Optional[List[str]],
        typer.Option(
            "-p",
            "--path",
            help="Include only changes in specified paths (can be used multiple times)",
        ),
    ] = None,
    exclude_path: Annotated[
        Optional[List[str]],
        typer.Option(
            "-x",
            "--exclude-path",
            help="Exclude changes in specified paths (can be used multiple times)",
        ),
    ] = None,
    default_period: Annotated[
        str,
        typer.Option(
            "--default-period",
            help="Default time period for analysis if --since is not provided (default: 3 months ago)",
        ),
    ] = "3 months ago",
    force_version_mismatch: Annotated[
        bool,
        typer.Option(
            "--force-version-mismatch",
            help="Proceed with analysis even if the DataFrame version does not match the expected version.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="Enable verbose output (INFO level)"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("-d", "--debug", help="Enable debug output (DEBUG level)"),
    ] = False,
):
    """Main function"""
    setup_logging(debug=debug, verbose=verbose)
    logger.debug(f"CLI arguments: {locals()}")

    # Typer handles mutual exclusivity, but we still need to validate combinations
    # that Typer's mutually_exclusive_group doesn't cover (e.g., --author and --me)
    # Also, repo_path is an Argument, so it's not part of the mutually_exclusive_group for options.
    # We need to manually check if repo_path is used with --remote-url or --df-path.
    if repo_path != "." and (remote_url or df_path):
        logger.error(
            "Error: Cannot use repo_path with --remote-url or --df-path. Please choose only one source."
        )
        raise typer.Exit(1)

    # Create a dummy args object for _validate_arguments for now, or refactor _validate_arguments
    # For now, let's refactor _validate_arguments to accept individual parameters
    # or just inline the logic here.
    # Inlining for now to avoid further refactoring _validation.py in this step.
    if author and me:
        error_message = "Error: Cannot use both --author and --me options together"
        logger.error(error_message)
        print(error_message, file=sys.stderr)
        raise typer.Exit(1)

    # Create configuration object
    config = GitAnalysisConfig(
        _start_date_str=since,
        _end_date_str=until,
        author_query=author,
        use_current_user=me,
        merged_only=merges,
        include_paths=path,
        exclude_paths=exclude_path,
        default_period=default_period,
    )

    # Create a dummy args object for _load_dataframe and _gather_git_data
    # This is a temporary workaround. Ideally, _load_dataframe and _gather_git_data
    # should be refactored to accept individual parameters instead of an 'args' object.
    class Args:  # type: ignore
        def __init__(self):
            self.df_path = df_path
            self.repo_path = repo_path
            self.remote_url = remote_url
            self.remote_branch = remote_branch
            self.force_version_mismatch = force_version_mismatch

    cli_args = Args()

    git_log_data, status_code = _load_dataframe(cli_args, config)
    if status_code != 0:
        raise typer.Exit(status_code)

    if git_log_data is None:
        git_log_data, status_code = _gather_git_data(cli_args, config)
        if status_code != 0:
            raise typer.Exit(status_code)

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


if __name__ == "__main__":
    app()
