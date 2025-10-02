import pytest
import pandas as pd
import os
import subprocess
from collections import defaultdict
import re
from git2df import get_commits_df

# Helper function to create a dummy git repo
def create_dummy_repo(tmp_path):
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)

    # Commit 1
    (repo_path / "file1.txt").write_text("line1\nline2")
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

    # Commit 2 (Author One)
    subprocess.run(["git", "config", "user.email", "author1@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Author One"], cwd=repo_path, check=True)
    (repo_path / "file2.txt").write_text("new file")
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add file2"], cwd=repo_path, check=True)

    # Commit 3 (Author Two)
    subprocess.run(["git", "config", "user.email", "author2@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Author Two"], cwd=repo_path, check=True)
    (repo_path / "file1.txt").write_text("line1\nline2\nline3") # 1 added
    subprocess.run(["git", "add", "file1.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Modify file1"], cwd=repo_path, check=True)

    # Commit 4 (Author One, another commit)
    subprocess.run(["git", "config", "user.email", "author1@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Author One"], cwd=repo_path, check=True)
    (repo_path / "file2.txt").write_text("new file\nmore content") # 1 added
    subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Modify file2 again"], cwd=repo_path, check=True)

    return repo_path

def _parse_raw_git_log_for_comparison(raw_log_output: str) -> dict:
    """
    Parses raw git log output (with --numstat and --pretty format)
    to extract author stats for comparison.
    """
    authors = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'num_commits': 0,
        'commit_hashes': set() # Use set to count unique commits
    })

    current_commit_hash = None
    current_author_name = None
    current_author_email = None

    for line in raw_log_output.splitlines():
        line = line.strip()

        if not line:
            current_commit_hash = None
            current_author_name = None
            current_author_email = None
            continue

        if line.startswith('--'):
            parts = line.split('--')
            if len(parts) >= 5:
                current_commit_hash = parts[1]
                current_author_name = parts[2]
                current_author_email = parts[3]
                
                if current_author_email not in authors:
                    authors[current_author_email]['name'] = current_author_name
                authors[current_author_email]['num_commits'] += 1
                authors[current_author_email]['commit_hashes'].add(current_commit_hash)
        else:
            if current_commit_hash and current_author_email:
                stat_match = re.match(r'^(\d+|-)\t(\d+|-)\t', line)
                if stat_match:
                    added_str, deleted_str = stat_match.groups()
                    
                    added = 0 if added_str == '-' else int(added_str)
                    deleted = 0 if deleted_str == '-' else int(deleted_str)
                    
                    authors[current_author_email]['added'] += added
                    authors[current_author_email]['deleted'] += deleted
    
    # Convert commit_hashes set to count for num_commits if not already done
    # (This is a simplified parser, so num_commits is directly counted)
    # Also calculate total_diff
    for email, data in authors.items():
        data['total_diff'] = data['added'] + data['deleted']
        data['num_commits'] = len(data['commit_hashes'])
        del data['commit_hashes'] # Not needed for final comparison dict

    return authors

def test_get_commits_df_integration(tmp_path):
    """Integration test for get_commits_df using a dummy git repository."""
    repo_path = create_dummy_repo(tmp_path)

    # Get data from git2df library
    df = get_commits_df(str(repo_path))

    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    # Expected columns
    expected_columns = [
        'author_name',
        'author_email',
        'added',
        'deleted',
        'total_diff',
        'num_commits',
        'commit_hashes'
    ]
    assert all(col in df.columns for col in expected_columns)

    # Get raw git log output for comparison
    git_log_cmd = [
        'git', 'log',
        '--numstat',
        '--pretty=format:--%H--%an--%ae--%ad--%s',
        '--date=iso'
    ]
    raw_git_log = subprocess.run(git_log_cmd, cwd=repo_path, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore').stdout.strip()
    expected_author_stats = _parse_raw_git_log_for_comparison(raw_git_log)

    # Compare DataFrame results with raw git log parsing
    for email, expected_stats in expected_author_stats.items():
        df_row = df[df['author_email'] == email]
        assert not df_row.empty, f"Author {email} not found in DataFrame."
        assert len(df_row) == 1, f"Duplicate entries for author {email} in DataFrame."

        assert df_row['author_name'].iloc[0] == expected_stats['name']
        assert df_row['added'].iloc[0] == expected_stats['added']
        assert df_row['deleted'].iloc[0] == expected_stats['deleted']
        assert df_row['total_diff'].iloc[0] == expected_stats['total_diff']
        assert df_row['num_commits'].iloc[0] == expected_stats['num_commits']

    # Ensure no extra authors in DataFrame
    assert set(df['author_email'].unique()) == set(expected_author_stats.keys())
