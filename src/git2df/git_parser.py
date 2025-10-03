import re
from collections import defaultdict
from datetime import datetime

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

def _parse_git_data_internal(git_data: list[str]) -> list[dict]:
    """Parse git log data and extract commit details and file stats per commit."""
    commits_data = []
    current_commit = None
    current_files = []

    # Wrap iteration with tqdm if available
    iterable_git_data = tqdm(git_data, desc="Parsing git log") if TQDM_AVAILABLE else git_data

    for line in iterable_git_data:
        line = line.strip()

        if not line:
            # Empty line, usually separates commits or ends file stats
            if current_commit and current_files:
                # If we have a commit and files, add them to commits_data
                for file_info in current_files:
                    commit_record = current_commit.copy()
                    commit_record.update(file_info)
                    commits_data.append(commit_record)
                current_commit = None
                current_files = []
            continue

        if line.startswith('--'):
            # New commit entry
            if current_commit and current_files:
                # If we have a previous commit and its files, add them
                for file_info in current_files:
                    commit_record = current_commit.copy()
                    commit_record.update(file_info)
                    commits_data.append(commit_record)
            
            # Reset for the new commit
            current_commit = {}
            current_files = []

            parts = line.split('--')
            # Expected format: --%H--%P--%an--%ae--%ad--%s
            if len(parts) >= 7:
                commit_hash = parts[1]
                parent_hash = parts[2] if parts[2] else None # Parent hash can be empty for initial commit
                author_name = parts[3]
                author_email = parts[4]
                commit_date_str = parts[5]
                commit_message = parts[6]

                current_commit = {
                    'commit_hash': commit_hash,
                    'parent_hash': parent_hash,
                    'author_name': author_name,
                    'author_email': author_email,
                    'commit_date': datetime.fromisoformat(commit_date_str),
                    'commit_message': commit_message
                }
        else:
            # File stat line (format: added\\tdeleted\\tfilepath)
            if current_commit:
                stat_match = re.match(r'^(\d+|-)\t(\d+|-)\t(.+)$', line)
                if stat_match:
                    added_str, deleted_str, file_path = stat_match.groups()
                    
                    additions = 0 if added_str == '-' else int(added_str)
                    deletions = 0 if deleted_str == '-' else int(deleted_str)

                    # Determine change_type (simplified for now, can be expanded)
                    change_type = 'M' # Modified by default
                    if additions > 0 and deletions == 0:
                        change_type = 'A' # Added
                    elif additions == 0 and deletions > 0:
                        change_type = 'D' # Deleted
                    # 'R' for rename, 'C' for copy are harder to get with --numstat alone

                    current_files.append({
                        'file_paths': file_path,
                        'change_type': change_type,
                        'additions': additions,
                        'deletions': deletions
                    })
    
    # Add the last commit's data if any
    if current_commit and current_files:
        for file_info in current_files:
            commit_record = current_commit.copy()
            commit_record.update(file_info)
            commits_data.append(commit_record)
            
    return commits_data
