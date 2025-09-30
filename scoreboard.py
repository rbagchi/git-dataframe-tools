#!/usr/bin/env python3
"""
Git Author Ranking by Diff Size (Last 3 Months)
This script analyzes git history and ranks authors by total lines changed
"""

__version__ = "0.1.0"

import subprocess
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import re
import math
import argparse
from dataclasses import dataclass
from typing import Optional
from parsedatetime import Calendar

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Note: Install 'tqdm' for progress bars: pip install tqdm")

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
    default_period: Optional[str] = None # Changed from default_days
    
    def __post_init__(self):
        """Process and validate configuration after initialization"""
        # Set up date range
        self.start_date, self.end_date = self._get_date_range()
        
        # Handle current user lookup
        if self.use_current_user:
            name, email = self._get_current_git_user()
            if not name or not email:
                print_error("Error: Could not determine current git user.")
                print("Please ensure git is configured with 'git config user.name' and 'git config user.email'")
                sys.exit(1)
            self.author_query = email if email else name
            self.current_user_name = name
            self.current_user_email = email
    
    def _get_date_range(self):
        """Get date range for git log analysis"""
        cal = Calendar()

        if self.end_date is None:
            end_date = datetime.now()
        elif isinstance(self.end_date, str):
            parsed_end_date, parse_status = cal.parseDT(self.end_date)
            if parse_status == 0: # 0 means parsing failed
                print_error(f"Invalid end date format: {self.end_date}. Use YYYY-MM-DD or natural language (e.g., 'yesterday', 'last week').")
                sys.exit(1)
            end_date = parsed_end_date
        
        if self.start_date is None:
            if self.default_period:
                try:
                    time_delta = _parse_period_string(self.default_period)
                    start_date = end_date - time_delta
                except ValueError as e:
                    print_error(f"Error parsing default period: {e}")
                    sys.exit(1)
            else:
                start_date = end_date - timedelta(days=90)  # Default 3 months
        elif isinstance(self.start_date, str):
            parsed_start_date, parse_status = cal.parseDT(self.start_date)
            if parse_status == 0: # 0 means parsing failed
                print_error(f"Invalid start date format: {self.start_date}. Use YYYY-MM-DD or natural language (e.g., 'yesterday', 'last week').")
                sys.exit(1)
            start_date = parsed_start_date
        
        if start_date >= end_date:
            print_error("Start date must be before end date.")
            sys.exit(1)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def _get_current_git_user(self):
        """Get the current git user's name and email"""
        try:
            # Get git user name
            name_result = subprocess.run(['git', 'config', 'user.name'], 
                                       capture_output=True, text=True, check=True)
            name = name_result.stdout.strip()
            
            # Get git user email  
            email_result = subprocess.run(['git', 'config', 'user.email'], 
                                        capture_output=True, text=True, check=True)
            email = email_result.stdout.strip()
            
            return name, email
        except subprocess.CalledProcessError:
            return None, None
    
    def _get_main_branch(self):
        """Detect the main branch (origin/master or origin/main)"""
        try:
            # Check if origin/main exists
            result = subprocess.run(['git', 'rev-parse', '--verify', 'origin/main'], 
                                  capture_output=True, check=True)
            return 'origin/main'
        except subprocess.CalledProcessError:
            pass
        
        try:
            # Check if origin/master exists
            result = subprocess.run(['git', 'rev-parse', '--verify', 'origin/master'], 
                                  capture_output=True, check=True)
            return 'origin/master'
        except subprocess.CalledProcessError:
            pass
        
        # Fallback: try to detect default branch from remote
        try:
            result = subprocess.run(['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'], 
                                  capture_output=True, text=True, check=True)
            ref = result.stdout.strip()
            if ref.startswith('refs/remotes/'):
                return ref[13:]  # Remove 'refs/remotes/' prefix
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def _estimate_commit_count(self):
        """Estimate the number of commits for progress tracking"""
        try:
            cmd = ['git', 'rev-list', '--count']
            
            if self.merged_only:
                main_branch = self._get_main_branch()
                if main_branch:
                    cmd.append(main_branch)
                else:
                    return None
            else:
                cmd.append('HEAD')
            
            cmd.extend([
                f'--since={self.start_date}',
                f'--until={self.end_date}'
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return None
    
    def get_git_log_data(self):
        """Get git log data with numstat based on configuration"""
        try:
            cmd = ['git', 'log']
            
            if self.merged_only:
                main_branch = self._get_main_branch()
                if not main_branch:
                    print_error("Error: Could not detect main branch (origin/master or origin/main)")
                    print("Please ensure you have a remote 'origin' with a main/master branch.")
                    sys.exit(1)
                cmd.append(main_branch)
                print_success(f"Analyzing merged commits from {main_branch}")
            
            cmd.extend([
                f'--since={self.start_date}',
                f'--until={self.end_date}',
                '--pretty=format:%H|%an|%ae',
                '--numstat'
            ])
            
            # Add path filtering
            if self.include_paths or self.exclude_paths:
                cmd.append('--') # Separator for pathspecs
                if self.include_paths:
                    cmd.extend(self.include_paths)
                if self.exclude_paths:
                    # Git exclusion syntax: ':!path'
                    cmd.extend([f':!{p}' for p in self.exclude_paths])
            
            # Try to estimate commit count for progress bar
            commit_count = self._estimate_commit_count()
            if commit_count and commit_count > 100:  # Only show for substantial operations
                if TQDM_AVAILABLE:
                    return self._run_with_progress(cmd, commit_count)
                else:
                    print_success(f"Fetching {commit_count:,} commits (this may take a while...)")
            
            # Fallback to regular execution
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print_error(f"Error getting git log data: {e}")
            sys.exit(1)
    
    def _run_with_progress(self, cmd, estimated_commits):
        """Run git command with progress bar"""
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Create progress bar
        progress_bar = tqdm(
            total=estimated_commits,
            desc="Fetching git history",
            unit="commits",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} [{elapsed}<{remaining}, {rate_fmt}]",
            smoothing=0.1
        )
        
        # Read output line by line and count commits
        output_lines = []
        commits_seen = 0
        last_update = 0
        
        try:
            for line in iter(process.stdout.readline, ''):
                output_lines.append(line)
                
                # Count commit lines (they contain the pipe separator with hash|name|email)
                if '|' in line and len(line.split('|')) >= 3:
                    commits_seen += 1
                    
                    # Update progress bar every 10 commits or at the end
                    if commits_seen - last_update >= 10 or commits_seen >= estimated_commits:
                        update_amount = min(commits_seen - last_update, estimated_commits - last_update)
                        if update_amount > 0:
                            progress_bar.update(update_amount)
                            last_update += update_amount
            
            # Wait for process to complete
            process.wait()
            
            # Complete the progress bar
            if last_update < estimated_commits:
                progress_bar.update(estimated_commits - last_update)
            
            progress_bar.close()
            
            if process.returncode != 0:
                stderr_output = process.stderr.read() if process.stderr else ""
                raise subprocess.CalledProcessError(process.returncode, cmd, ''.join(output_lines), stderr_output)
            
            return ''.join(output_lines)
            
        except Exception as e:
            progress_bar.close()
            process.terminate()
            raise e
    
    def get_commit_summary(self):
        """Get commit count summary using git shortlog based on configuration"""
        try:
            cmd = ['git', 'shortlog']
            
            if self.merged_only:
                main_branch = self._get_main_branch()
                if main_branch:
                    cmd.append(main_branch)
            
            cmd.extend([
                f'--since={self.start_date}',
                f'--until={self.end_date}',
                '--numbered', '--summary'
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError:
            return "Could not generate commit summary"
    
    def get_analysis_description(self):
        """Get a human-readable description of the analysis being performed"""
        analysis_type = "merged commits" if self.merged_only else "commits"
        return f"Analyzing {analysis_type} from {self.start_date} to {self.end_date}"
    
    def is_author_specific(self):
        """Check if this is an author-specific analysis"""
        return self.author_query is not None

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

def check_git_repo():
    """Check if we're in a git repository"""
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], 
                      capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def parse_git_data(git_data):
    """Parse git log data and calculate stats per author"""
    authors = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set()
    })
    
    current_commit = None
    current_author_name = None
    current_author_email = None
    
    for line in git_data.split('\n'):
        line = line.strip()
        
        if not line:
            # Empty line - reset current commit info
            current_commit = None
            current_author_name = None
            current_author_email = None
            continue
            
        if '|' in line:
            # Commit info line
            parts = line.split('|')
            if len(parts) >= 3:
                current_commit = parts[0]
                current_author_name = parts[1]
                current_author_email = parts[2]
            continue
            
        # File stat line (format: added\tdeleted\tfilename)
        if current_commit and current_author_name and current_author_email:
            # Match lines that start with numbers or dashes (for binary files)
            stat_match = re.match(r'^(\d+|-)\t(\d+|-)\t', line)
            if stat_match:
                added_str, deleted_str = stat_match.groups()
                
                added = 0 if added_str == '-' else int(added_str)
                deleted = 0 if deleted_str == '-' else int(deleted_str)
                
                authors[current_author_email]['name'] = current_author_name
                authors[current_author_email]['added'] += added
                authors[current_author_email]['deleted'] += deleted
                authors[current_author_email]['total'] += (added + deleted)
                authors[current_author_email]['commits'].add(current_commit)
    
    return authors

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
        # Approximate months to 30 days for simplicity in timedelta
        return timedelta(days=value * 30)
    elif unit == 'year':
        # Approximate years to 365 days for simplicity in timedelta
        return timedelta(days=value * 365)
    else:
        # Should not happen due to regex, but for safety
        raise ValueError(f"Unknown unit: {unit}")

def _prepare_author_data(authors_dict):
    """Prepares author data with ranks and deciles."""
    author_list = []
    for email, stats in authors_dict.items():
        author_list.append({
            'email': email,
            'name': stats['name'],
            'added': stats['added'],
            'deleted': stats['deleted'],
            'total': stats['total'],
            'commits': len(stats['commits'])
        })

    if not author_list:
        return []

    # Sort by total diff size (descending) for initial ranking
    author_list.sort(key=lambda x: x['total'], reverse=True)

    # Calculate ranks and deciles for diff size
    n = len(author_list)
    
    # Assign ranks and deciles based on diff values
    current_rank = 1
    current_decile = 1
    for i in range(n):
        if i > 0 and author_list[i]['total'] < author_list[i-1]['total']:
            current_rank = i + 1
            current_decile = min(10, math.ceil(current_rank * 10 / n))
        
        author_list[i]['rank'] = current_rank
        author_list[i]['diff_decile'] = current_decile

    # Sort by commit count (descending) for commit decile calculation
    author_list.sort(key=lambda x: x['commits'], reverse=True)

    # Assign deciles based on commit values
    current_rank = 1
    current_decile = 1
    for i in range(n):
        if i > 0 and author_list[i]['commits'] < author_list[i-1]['commits']:
            current_rank = i + 1
            current_decile = min(10, math.ceil(current_rank * 10 / n))
        
        author_list[i]['commit_decile'] = current_decile
    
    # Re-sort by total diff size for consistent output order
    author_list.sort(key=lambda x: x['total'], reverse=True)

    return author_list

def find_author_stats(authors_dict, config: GitAnalysisConfig):
    """Find and display stats for a specific author"""
    author_list = _prepare_author_data(authors_dict)
    
    if not author_list:
        analysis_type = "merged commits" if config.merged_only else "commits"
        print_warning(f"No {analysis_type} found in the specified time period.")
        return
    
    # Find matching authors
    query_lower = config.author_query.lower()
    matches = []
    for author in author_list:
        if (query_lower in author['name'].lower() or 
            query_lower in author['email'].lower()):
            matches.append(author)
    
    if not matches:
        print_error(f"No authors found matching '{config.author_query}'")
        print("\nSuggestion: Try a partial match like first name, last name, or email domain.")
        return
    
    print()
    analysis_type = "merged commits" if config.merged_only else "commits"
    print_header(f"Author Stats for '{config.author_query}' ({analysis_type})")
    print_header(f"Analysis period: {config.start_date} to {config.end_date}")
    print()
    
    if len(matches) > 1:
        print_warning(f"Found {len(matches)} matching authors:")
        print()
    
    for author in matches:
        print_success(f"Author: {author['name']} <{author['email']}>")
        print(f"  Rank:          #{author['rank']} of {len(author_list)} authors")
        print(f"  Lines Added:   {author['added']:,}")
        print(f"  Lines Deleted: {author['deleted']:,}")
        print(f"  Total Diff:    {author['total']:,}")
        print(f"  Commits:       {author['commits']}")
        print(f"  Diff Decile:   {author['diff_decile']} (1=top 10%, 10=bottom 10%)")
        print(f"  Commit Decile: {author['commit_decile']} (1=top 10%, 10=bottom 10%)")
        
        # Calculate percentile more precisely
        percentile = (author['rank'] - 1) / len(author_list) * 100
        print(f"  Percentile:    Top {percentile:.1f}%")
        
        if author['commits'] > 0:
            avg_diff_per_commit = author['total'] / author['commits']
            print(f"  Avg Diff/Commit: {avg_diff_per_commit:.0f} lines")
        
        print()

def print_ranking(authors_dict, config: GitAnalysisConfig):
    """Print the author ranking"""
    print()
    print_header("Git Author Ranking by Diff Size")
    print_header(config.get_analysis_description())
    print()
    
    author_list = _prepare_author_data(authors_dict)
    
    if not author_list:
        print_warning("No commits found in the last 3 months.")
        return
    
    # Print table header
    print(f"{'Rank':>4} {'Author':<45} {'Lines Added':>11} {'Lines Deleted':>12} {'Total Diff':>11} {'Commits':>7} {'Diff D':>6} {'Comm D':>6}")
    print(f"{'-'*4:>4} {'-'*45:<45} {'-'*11:>11} {'-'*12:>12} {'-'*11:>11} {'-'*7:>7} {'-'*6:>6} {'-'*6:>6}")
    
    # Print results
    for author in author_list:
        author_display = f"{author['name']} <{author['email']}>"
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


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Analyze git history and rank authors by total diff size',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                           # Last 3 months (default)
  %(prog)s --start 2025-06-01        # From June 1st to now
  %(prog)s --end 2025-08-31          # Last 3 months before Aug 31st
  %(prog)s --start 2025-06-01 --end 2025-08-31  # Specific date range
  %(prog)s --author "john.doe"       # Show stats for specific author
  %(prog)s --me                      # Show your own stats
  %(prog)s --me --start 2025-06-01   # Your stats for date range
  %(prog)s --merged-only             # Only merged commits (production code)
  %(prog)s --me --merged-only        # Your merged contributions only

Date format: YYYY-MM-DD
'''
    )
    
    parser.add_argument(
        '--start', '-s',
        type=str,
        help='Start date for analysis (YYYY-MM-DD). Default: 3 months ago'
    )
    
    parser.add_argument(
        '--end', '-e', 
        type=str,
        help='End date for analysis (YYYY-MM-DD). Default: today'
    )
    
    parser.add_argument(
        '--author', '-a',
        type=str,
        help='Show detailed stats for a specific author (partial name/email match)'
    )
    
    parser.add_argument(
        '--me', '-m',
        action='store_true',
        help='Show detailed stats for the current git user (equivalent to --author with your git config)'
    )
    
    parser.add_argument(
        '--merged-only',
        action='store_true',
        help='Only analyze commits that have been merged to the main branch (origin/master or origin/main)'
    )
    
    parser.add_argument(
        '--default-period',
        type=str,
        help='Default period to look back if --start is not specified (e.g., "3 months", "1 year"). Default: "3 months".'
    )
    
    parser.add_argument(
        '--path',
        nargs='*',
        help='Include only changes to files within these paths (e.g., "src/frontend" "src/backend"). Can be specified multiple times.'
    )
    
    parser.add_argument(
        '--exclude-path',
        nargs='*',
        help='Exclude changes to files within these paths (e.g., "docs" "tests"). Can be specified multiple times.'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    if not check_git_repo():
        print_error("Error: Not in a git repository")
        sys.exit(1)
    
    # Validate mutually exclusive arguments
    if args.author and args.me:
        print_error("Error: Cannot use both --author and --me options together")
        sys.exit(1)
    
    # Create configuration object
    config = GitAnalysisConfig(
        start_date=args.start,
        end_date=args.end,
        author_query=args.author,
        use_current_user=args.me,
        merged_only=args.merged_only,
        include_paths=args.path,
        exclude_paths=args.exclude_path,
        default_period=args.default_period
    )
    
    print_success("Gathering commit data...")
    git_data = config.get_git_log_data()
    
    print_success("Processing commits...")
    authors = parse_git_data(git_data)
    
    # If author-specific analysis requested, show only their stats
    if config.is_author_specific():
        if config.use_current_user:
            print_success(f"Looking up stats for current user: {config.current_user_name} <{config.current_user_email}>")
        find_author_stats(authors, config)
        return
    
    # Otherwise show full ranking
    print_ranking(authors, config)
    
    print()
    print_header("Commit Count Summary:")
    print(config.get_commit_summary())
    
    print_success("Analysis complete!")

if __name__ == "__main__":
    main()
