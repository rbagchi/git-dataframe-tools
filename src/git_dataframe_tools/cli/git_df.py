#!/usr/bin/env python3
"""
Git DataFrame Extractor: Extracts filtered Git commit data and saves it to a Parquet file.
"""

import argparse
import sys
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import logging

from git2df import get_commits_df
from git_dataframe_tools.logger import setup_logging

DATA_VERSION = "1.0"  # Major version of the data format

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Extracts filtered Git commit data and saves it to a Parquet file as a Pandas DataFrame.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    repo_group = parser.add_mutually_exclusive_group(required=True)
    repo_group.add_argument(
        "--repo-path",
        default=".",
        help="Path to the Git repository (default: current directory). This cannot be used with --remote-url.",
    )
    repo_group.add_argument(
        "--remote-url",
        help="URL of the remote Git repository to analyze (e.g., https://github.com/user/repo). This cannot be used with --repo-path.",
    )
    parser.add_argument(
        "--remote-branch",
        default="main",
        help="Branch of the remote repository to analyze (default: main). Only applicable with --remote-url.",
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
        "-g", "--grep", help='Filter by commit message (e.g., "fix", "feature")'
    )
    parser.add_argument(
        "-m",
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
        "-o",
        "--output",
        required=True,
        help='Output Parquet file path (e.g., "commits.parquet")',
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


def run_git_df_cli(args):
    setup_logging(debug=args.debug, verbose=args.verbose)
    logger.debug(f"CLI arguments: {args}")

    # Ensure the repository path exists if a local repo is used
    if not args.remote_url and args.repo_path and not os.path.isdir(args.repo_path):
        logger.error(
            f"Repository path '{args.repo_path}' does not exist or is not a directory."
        )
        sys.exit(1)

    if args.remote_url:
        logger.info(f"Extracting commit data from remote '{args.remote_url}' branch '{args.remote_branch}'...")
        repo_path_arg = None # Not used for remote
    else:
        logger.info(f"Extracting commit data from local '{args.repo_path}'...")
        repo_path_arg = args.repo_path

    try:
        commits_df = get_commits_df(
            repo_path=repo_path_arg,
            remote_url=args.remote_url,
            remote_branch=args.remote_branch,
            since=args.since,
            until=args.until,
            author=args.author,
            grep=args.grep,
            merged_only=args.merges,
            include_paths=args.path,
            exclude_paths=args.exclude_path,
        )
    except Exception as e:
        logger.error(f"Error fetching git log data: {e}")
        sys.exit(1)

    if commits_df.empty:
        logger.warning(
            f"No commits found for the specified criteria in '{args.repo_path}'."
        )
        # If no commits are found, we should still create an empty parquet file
        # to indicate that the operation was successful but yielded no data.
        # This prevents downstream processes from failing due to missing files.
        try:
            # Create an empty PyArrow Table with metadata
            empty_df = pd.DataFrame()
            table = pa.Table.from_pandas(empty_df)
            custom_metadata = {
                "data_version": DATA_VERSION,
                "description": "Git commit data extracted by git-df CLI",
            }
            metadata_bytes = {
                k.encode(): str(v).encode() for k, v in custom_metadata.items()
            }

            # Create a PyArrow Schema with metadata for an empty DataFrame
            empty_df = pd.DataFrame()
            temp_table = pa.Table.from_pandas(empty_df)
            new_schema = temp_table.schema.with_metadata(metadata_bytes)

            # Convert pandas DataFrame to PyArrow Table with the new schema
            table = pa.Table.from_pandas(empty_df, schema=new_schema)
            pq.write_table(table, args.output)
            logger.info(
                f"Created empty Parquet file at '{args.output}' as no commits were found."
            )
        except Exception as e:
            logger.error(f"Error creating empty Parquet file: {e}")
            sys.exit(1)
        return

    logger.info(f"Saving {len(commits_df)} commits to '{args.output}'...")
    try:
        # Convert pandas DataFrame to PyArrow Table
        table = pa.Table.from_pandas(commits_df)

        # Define custom metadata
        custom_metadata = {
            "data_version": DATA_VERSION,
            "description": "Git commit data extracted by git-df CLI",
        }

        # Add custom metadata to the table schema
        metadata_bytes = {
            k.encode(): str(v).encode() for k, v in custom_metadata.items()
        }
        # Create a PyArrow Schema with metadata
        # Get the schema from the pandas DataFrame first
        temp_table = pa.Table.from_pandas(commits_df)
        new_schema = temp_table.schema.with_metadata(metadata_bytes)

        # Convert pandas DataFrame to PyArrow Table with the new schema
        table = pa.Table.from_pandas(commits_df, schema=new_schema)

        # Write the PyArrow Table to a Parquet file
        pq.write_table(table, args.output)
        logger.info(f"Successfully saved commit data to '{args.output}'.")
    except Exception as e:
        logger.error(f"Error saving data to Parquet: {e}")
        sys.exit(1)


def main():
    args = parse_arguments()
    run_git_df_cli(args)


if __name__ == "__main__":
    main()
