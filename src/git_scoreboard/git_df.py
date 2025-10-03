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

from git2df import get_commits_df

DATA_VERSION = "1.0"  # Major version of the data format


# Helper functions for colored output
def print_success(message):
    print(f"\033[92m\033[1mSUCCESS:\033[0m {message}")


def print_error(message):
    print(f"\033[91m\033[1mERROR:\033[0m {message}", file=sys.stderr)


def print_warning(message):
    print(f"\033[93m\033[1mWARNING:\033[0m {message}")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Extracts filtered Git commit data and saves it to a Parquet file as a Pandas DataFrame.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--repo-path",
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

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Ensure the repository path exists
    if not os.path.isdir(args.repo_path):
        print_error(
            f"Error: Repository path '{args.repo_path}' does not exist or is not a directory."
        )
        sys.exit(1)

    print_success(f"Extracting commit data from '{args.repo_path}'...")
    try:
        commits_df = get_commits_df(
            repo_path=args.repo_path,
            since=args.since,
            until=args.until,
            author=args.author,
            grep=args.grep,
            merged_only=args.merges,
            include_paths=args.path,
            exclude_paths=args.exclude_path,
        )
    except Exception as e:
        print_error(f"Error fetching git log data: {e}")
        sys.exit(1)

    if commits_df.empty:
        print_warning(
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
            print_success(
                f"Created empty Parquet file at '{args.output}' as no commits were found."
            )
        except Exception as e:
            print_error(f"Error creating empty Parquet file: {e}")
            sys.exit(1)
        return

    print_success(f"Saving {len(commits_df)} commits to '{args.output}'...")
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
        print_success(f"Successfully saved commit data to '{args.output}'.")
    except Exception as e:
        print_error(f"Error saving data to Parquet: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
else:
    # This allows the script to be run via `uv run python -m src.git_scoreboard.git_extract_commits`
    # or similar module-based execution, which `uv run python <script.py>` does.
    main()
