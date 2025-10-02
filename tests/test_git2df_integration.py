import pytest
import pandas as pd
import os
import subprocess
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

def test_get_commits_df_integration(tmp_path):
    """Integration test for get_commits_df using a dummy git repository."""
    repo_path = create_dummy_repo(tmp_path)

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

    # Verify data for Author One
    author_one_df = df[df['author_email'] == 'author1@example.com']
    assert len(author_one_df) == 1
    assert author_one_df['author_name'].iloc[0] == 'Author One'
    assert author_one_df['added'].iloc[0] == 3 # 2 from file2.txt creation + 1 from file2.txt modification
    assert author_one_df['deleted'].iloc[0] == 1
    assert author_one_df['total_diff'].iloc[0] == 4
    assert author_one_df['num_commits'].iloc[0] == 2 # Two commits by Author One

    # Verify data for Author Two
    author_two_df = df[df['author_email'] == 'author2@example.com']
    assert len(author_two_df) == 1
    assert author_two_df['author_name'].iloc[0] == 'Author Two'
    assert author_two_df['added'].iloc[0] == 2
    assert author_two_df['deleted'].iloc[0] == 1
    assert author_two_df['total_diff'].iloc[0] == 3
    assert author_two_df['num_commits'].iloc[0] == 1 # One commit by Author Two

    # Verify data for Test User (initial commit)
    test_user_df = df[df['author_email'] == 'test@example.com']
    assert len(test_user_df) == 1
    assert test_user_df['author_name'].iloc[0] == 'Test User'
    assert test_user_df['added'].iloc[0] == 2
    assert test_user_df['deleted'].iloc[0] == 0
    assert test_user_df['total_diff'].iloc[0] == 2
    assert test_user_df['num_commits'].iloc[0] == 1 # One commit by Test User
