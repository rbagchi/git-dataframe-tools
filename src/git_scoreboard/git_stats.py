import re
from collections import defaultdict
import math
import pandas as pd

def _parse_git_data_internal(git_data_df: pd.DataFrame):
    """Parse git log data from DataFrame and calculate stats per author"""
    authors = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set()
    })
    
    if git_data_df.empty:
        return authors

    for _, row in git_data_df.iterrows():
        author_email = row['author_email']
        author_name = row['author_name']
        commit_hash = row['hash']
        added = row['added']
        deleted = row['deleted']

        authors[author_email]['name'] = author_name
        authors[author_email]['added'] += added
        authors[author_email]['deleted'] += deleted
        authors[author_email]['total'] += (added + deleted)
        authors[author_email]['commits'].add(commit_hash)
    
    return authors

def parse_git_log(git_data_df: pd.DataFrame) -> list[dict]:
    """Parses git data from DataFrame and prepares author statistics."""
    authors_dict = _parse_git_data_internal(git_data_df)
    return _prepare_author_data(authors_dict)

def _prepare_author_data(authors_dict):
    """Prepares author data with ranks and deciles."""
    author_list = []
    for email, stats in authors_dict.items():
        author_list.append({
            'author_email': email,
            'author_name': stats['name'],
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

def find_author_stats(author_stats: list[dict], author_query: str) -> list[dict]:
    """Finds and returns stats for a specific author from the author statistics list."""
    if not author_stats:
        return []
    
    # Find matching authors
    query_parts = [p.strip().lower() for p in author_query.split('|')]
    matches = []
    for author in author_stats:
        for part in query_parts:
            if (part in author['author_name'].lower() or 
                part in author['author_email'].lower()):
                matches.append(author)
                break # Match found for this author, move to next author
    
    return matches

def get_ranking(author_stats: list[dict]) -> list[dict]:
    """Returns the author statistics list sorted by total diff for printing."""
    if not author_stats:
        return []
    return sorted(author_stats, key=lambda x: x['total'], reverse=True)