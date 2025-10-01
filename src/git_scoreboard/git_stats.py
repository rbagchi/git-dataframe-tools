import re
from collections import defaultdict
from datetime import timedelta
import math
from dateutil.relativedelta import relativedelta

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
    current_commit_message = None
    
    for line in git_data.split('\n'):
        line = line.strip()
        
        if not line:
            # Empty line - reset current commit info
            current_commit = None
            current_author_name = None
            current_author_email = None
            current_commit_message = None
            continue
            
        if '|' in line:
            # Commit info line
            parts = line.split('|')
            if len(parts) >= 4:
                current_commit = parts[0]
                current_author_name = parts[1]
                current_author_email = parts[2]
                current_commit_message = parts[3]
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
        return relativedelta(months=value)
    elif unit == 'year':
        return relativedelta(years=value)
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

def find_author_stats(authors_dict, config):
    """Find and display stats for a specific author"""
    author_list = _prepare_author_data(authors_dict)
    
    if not author_list:
        analysis_type = "merged commits" if config.merged_only else "commits"
        # print_warning(f"No {analysis_type} found in the specified time period.") # Removed print_warning
        return # Return None or raise an exception instead of printing
    
    # Find matching authors
    query_lower = config.author_query.lower()
    matches = []
    for author in author_list:
        if (query_lower in author['name'].lower() or 
            query_lower in author['email'].lower()):
            matches.append(author)
    
    if not matches:
        # print_error(f"No authors found matching '{config.author_query}'") # Removed print_error
        # print("\nSuggestion: Try a partial match like first name, last name, or email domain.") # Removed print
        return # Return None or raise an exception instead of printing
    
    # The actual printing logic will be handled by the main script
    return matches # Return the matches for external printing

def print_ranking(authors_dict, config):
    """Print the author ranking"""
    # The actual printing logic will be handled by the main script
    return _prepare_author_data(authors_dict) # Return the prepared data for external printing
