import re
from collections import defaultdict

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

def _parse_git_data_internal(git_data: list[str]) -> dict:
    """Parse git log data and extract raw commit and file stats per author."""
    authors = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set(),
        'commit_hashes': [] # To store individual commit hashes for DataFrame
    })
    
    current_commit_hash = None
    current_author_name = None
    current_author_email = None
    
    # Wrap iteration with tqdm if available
    iterable_git_data = tqdm(git_data, desc="Parsing git log") if TQDM_AVAILABLE else git_data

    for line in iterable_git_data:
        line = line.strip()
        
        if not line:
            # Empty line - reset current commit info
            current_commit_hash = None
            current_author_name = None
            current_author_email = None
            continue
            
        if line.startswith('--'):
            # Commit info line (format: --HASH--AUTHOR_NAME--AUTHOR_EMAIL--DATE--SUBJECT)
            parts = line.split('--')
            if len(parts) >= 5:
                current_commit_hash = parts[1]
                current_author_name = parts[2]
                current_author_email = parts[3]
                authors[current_author_email]['name'] = current_author_name # Moved this line
                
                # Always add to the set of commits for this author
                authors[current_author_email]['commits'].add(current_commit_hash)
                
                # Add to the list of commit_hashes only if it's a new commit for this author
                if current_commit_hash not in authors[current_author_email]['commit_hashes']:
                    authors[current_author_email]['commit_hashes'].append(current_commit_hash)
            # DO NOT continue here, process file stats if any
        else: # This is a file stat line
            # File stat line (format: added\tdeleted\tfilename)
            if current_commit_hash and current_author_name and current_author_email:
                # Match lines that start with numbers or dashes (for binary files)
                stat_match = re.match(r'^(\d+|-)\t(\d+|-)\t', line)
                if stat_match:
                    added_str, deleted_str = stat_match.groups()
                    
                    added = 0 if added_str == '-' else int(added_str)
                    deleted = 0 if deleted_str == '-' else int(deleted_str)
                    
                    # authors[current_author_email]['name'] = current_author_name # Removed this line
                    authors[current_author_email]['added'] += added
                    authors[current_author_email]['deleted'] += deleted
                    authors[current_author_email]['total'] += (added + deleted)
    
    return authors
