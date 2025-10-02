#!/usr/bin/env python3
"""
Git Commit Extractor: Extracts filtered commit data and saves it to a Parquet file.
"""

import argparse
import sys
import os

from git_scoreboard.config_models import GitAnalysisConfig, print_success, print_error, print_warning
from git_scoreboard.git_utils import get_git_data_from_config

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Extracts filtered Git commit data and saves it to a Parquet file.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'repo_path',
        nargs='?',
        default='.',
        help='Path to the Git repository (default: current directory).'
    )
    parser.add_argument(
        '-S', '--since',
        help='Start date for analysis (e.g., "2023-01-01", "3 months ago", "1 year ago")'
    )
    parser.add_argument(
        '-U', '--until',
        help='End date for analysis (e.g., "2023-03-31", "now")'
    )
    parser.add_argument(
        '-a', '--author',
        help='Filter by author name or email (e.g., "John Doe", "john@example.com")'
    )
    parser.add_argument(
        '-g', '--grep',
        help='Filter by commit message (e.g., "fix", "feature")'
    )
    parser.add_argument(
        '-m', '--merges',
        action='store_true',
        help='Only include commits that are merged into the current branch (e.g., via pull requests)'
    )
    parser.add_argument(
        '-p', '--path',
        action='append',
        help='Include only changes in specified paths (can be used multiple times)'
    )
    parser.add_argument(
        '-x', '--exclude-path',
        action='append',
        help='Exclude changes in specified paths (can be used multiple times)'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output Parquet file path (e.g., "commits.parquet")'
    )
    parser.add_argument(
        '--default-period',
        default='3 months',
        help='Default period if --since or --until are not specified (e.g., "3 months", "1 year")'
    )
    
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Ensure the repository path exists
    if not os.path.isdir(args.repo_path):
        print_error(f"Error: Repository path '{args.repo_path}' does not exist or is not a directory.")
        sys.exit(1)
    
    # Create configuration object
    config = GitAnalysisConfig(
        start_date=args.since,
        end_date=args.until,
        author_query=args.author,
        merged_only=args.merges,
        include_paths=args.path,
        exclude_paths=args.exclude_path,
        default_period=args.default_period
    )

    print_success(f"Extracting commit data from '{args.repo_path}'...")
    try:
        commits_df = get_git_data_from_config(config, repo_path=args.repo_path)
    except SystemExit: # get_git_data_from_config can call sys.exit
        return

    if commits_df.empty:
        print_warning(f"No commits found for the specified criteria in '{args.repo_path}'.")
        return

    print_success(f"Saving {len(commits_df)} commits to '{args.output}'...")
    try:
        commits_df.to_parquet(args.output, index=False)
        print_success(f"Successfully saved commit data to '{args.output}'.")
    except Exception as e:
        print_error(f"Error saving data to Parquet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
