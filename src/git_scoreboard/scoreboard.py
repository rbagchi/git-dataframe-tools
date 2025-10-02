#!/usr/bin/env python3
"""
Git Author Ranking by Diff Size (Last 3 Months)
This script analyzes git history and ranks authors by total lines changed
"""

__version__ = "0.1.0"

import argparse

from git_scoreboard.config_models import GitAnalysisConfig, _parse_period_string, print_success, print_error, print_warning, print_header
import git_scoreboard.git_stats as git_stats_module
import git_scoreboard.git_stats_pandas as git_stats_pandas_module

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Note: Install 'tqdm' for progress bars: pip install tqdm")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Git Author Ranking by Diff Size (Last 3 Months)',
        formatter_class=argparse.RawTextHelpFormatter
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
        '-m', '--me',
        action='store_true',
        help='Filter by current git user (uses git config user.name and user.email)'
    )
    parser.add_argument(
        '--merges',
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
        '--default-period',
        default='3 months',
        help='Default period if --since or --until are not specified (e.g., "3 months", "1 year")'
    )
    parser.add_argument(
        '--pandas',
        action='store_true',
        help='Use the pandas-based statistics engine (experimental)'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # Validate mutually exclusive arguments
    if args.author and args.me:
        print_error("Error: Cannot use both --author and --me options together")
        return
    
    # Create configuration object
    config = GitAnalysisConfig(
        start_date=args.since,
        end_date=args.until,
        author_query=args.author,
        use_current_user=args.me,
        merged_only=args.merges,
        include_paths=args.path,
        exclude_paths=args.exclude_path,
        default_period=args.default_period
    )
    
    # Select the statistics module based on arguments
    if args.pandas:
        stats_module = git_stats_pandas_module
    else:
        stats_module = git_stats_module

    print_success("Gathering commit data...")
    git_log_data = config.get_git_log_data()
    
    print_success("Processing commits...")
    author_stats = stats_module.parse_git_log(git_log_data)
    
    # If author-specific analysis requested, show only their stats
    if config.is_author_specific():
        if config.use_current_user:
            print_success(f"Looking up stats for current user: {config.current_user_name} <{config.current_user_email}>")
        
        author_matches = stats_module.find_author_stats(author_stats, config.author_query)
        if not author_matches:
            analysis_type = "merged commits" if config.merged_only else "commits"
            print_warning(f"No {analysis_type} found in the specified time period.")
            print_error(f"No authors found matching '{config.author_query}'")
            print("Suggestion: Try a partial match like first name, last name, or email domain.")
            return
        
        print()
        analysis_type = "merged commits" if config.merged_only else "commits"
        print_header(f"Author Stats for '{config.author_query}' ({analysis_type})")
        print_header(f"Analysis period: {config.start_date} to {config.end_date}")
        print()
        
        if len(author_matches) > 1:
            print_warning(f"Found {len(author_matches)} matching authors:")
            print()
        
        for author in author_matches:
            print_success(f"Author: {author['author_name']} <{author['author_email']}>")
            print(f"  Rank:          #{author['rank']} of {len(author_matches)} authors") # Changed len(author_list) to len(author_matches)
            print(f"  Lines Added:   {author['added']:,}")
            print(f"  Lines Deleted: {author['deleted']:,}")
            print(f"  Total Diff:    {author['total']:,}")
            print(f"  Commits:       {author['commits']}")
            print(f"  Diff Decile:   {author['diff_decile']} (1=top 10%, 10=bottom 10%)")
            print(f"  Commit Decile: {author['commit_decile']} (1=top 10%, 10=bottom 10%)")
            
            # Calculate percentile more precisely
            percentile = (author['rank'] - 1) / len(author_matches) * 100 # Changed len(author_list) to len(author_matches)
            print(f"  Percentile:    Top {percentile:.1f}%")
            
            if author['commits'] > 0:
                avg_diff_per_commit = author['total'] / author['commits']
                print(f"  Avg Diff/Commit: {avg_diff_per_commit:.0f} lines")
            
            print()
        return
    
    # Otherwise show full ranking
    author_list = stats_module.get_ranking(author_stats)
    
    print()
    print_header("Git Author Ranking by Diff Size")
    print_header(config.get_analysis_description())
    print()
    
    if not author_list:
        print_warning("No commits found in the last 3 months.")
        return
    
    # Print table header
    print(f"{'Rank':>4} {'Author':<45} {'Lines Added':>11} {'Lines Deleted':>12} {'Total Diff':>11} {'Commits':>7} {'Diff D':>6} {'Comm D':>6}")
    print(f"{'-'*4:>4} {'-'*45:<45} {'-'*11:>11} {'-'*12:>12} {'-'*11:>11} {'-'*7:>7} {'-'*6:>6} {'-'*6:>6}")
    
    # Print results
    for author in author_list:
        author_display = f"{author['author_name']} <{author['author_email']}>"
        # Truncate author display if too long
        if len(author_display) > 45:
            author_display = author_display[:42] + "..."
            
        added_str = str(author['added']) if author['added'] > 0 else '-'
        deleted_str = str(author['deleted']) if author['deleted'] > 0 else '-'
        
        print(f"{author['rank']:>4} {author_display:<45} {added_str:>11} {deleted_str:>12} {author['total']:>11} {author['commits']:>7} {author['diff_decile']:>6} {author['commit_decile']:>6}")
    
    # Print decile distribution summary
    print(f"\nDiff Size Decile Distribution:")
    print(f"{'Decile':>6} {'Diff Size Range':>25} {'Authors':>8}")
    print(f"{'-'*6:>6} {'-'*25:>25} {'-'*8:>8}")
    
    for decile in range(1, 11):
        diff_authors = [a for a in author_list if a['diff_decile'] == decile]
        if diff_authors:
            min_diff = min(a['total'] for a in diff_authors)
            max_diff = max(a['total'] for a in diff_authors)
            diff_range = f"{min_diff:,}-{max_diff:,}" if min_diff != max_diff else f"{min_diff:,}"
            print(f"{decile:>6} {diff_range:>25} {len(diff_authors):>8}")
    
    print(f"\nCommit Count Decile Distribution:")
    print(f"{'Decile':>6} {'Commit Range':>15} {'Authors':>8}")
    print(f"{'-'*6:>6} {'-'*15:>15} {'-'*8:>8}")
    
    for decile in range(1, 11):
        commit_authors = [a for a in author_list if a['commit_decile'] == decile]
        if commit_authors:
            min_commits = min(a['commits'] for a in commit_authors)
            max_commits = max(a['commits'] for a in commit_authors)
            commit_range = f"{min_commits}-{max_commits}" if min_commits != max_commits else f"{min_commits}"
            print(f"{decile:>6} {commit_range:>15} {len(commit_authors):>8}")
    
    print(f"\nSummary:")
    print(f"- Ranking based on total lines changed (additions + deletions)")
    print(f"- Diff D = Diff Size Decile (1=top 10%, 10=bottom 10%)")
    print(f"- Comm D = Commit Count Decile (1=top 10%, 10=bottom 10%)")
    print(f"- Analysis period: from {config.start_date} to {config.end_date}")
    print(f"- Total unique authors: {len(author_list)}")

if __name__ == "__main__":
    main()
