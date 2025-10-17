import pytest
from git2df.backend_interface import GitBackend
from git2df.pygit2_backend import Pygit2Backend
from git2df.git_parser import GitLogEntry
from datetime import datetime, timedelta, timezone
import time

def test_pygit2_backend_initialization():
    backend = Pygit2Backend(repo_path=".")
    assert isinstance(backend, GitBackend)

@pytest.mark.parametrize(
    "pygit2_repo", # Use pygit2_repo fixture
    [
        [
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Initial commit",
                "files": {"file1.txt": "hello world"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Second commit",
                "files": {"file2.txt": "another file"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Dev User",
                "author_email": "dev@example.com",
                "message": "Third commit by Dev User",
                "files": {"file1.txt": "hello world again"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
            },
        ]
    ],
    indirect=True,
)
def test_get_log_entries_no_filters(pygit2_repo): # Use pygit2_repo fixture
    repo_path = pygit2_repo
    backend = Pygit2Backend(repo_path=repo_path)
    log_entries = backend.get_log_entries()

    assert isinstance(log_entries, list)
    assert len(log_entries) == 4 # Initial commit + 3 parameterized commits
    assert all(isinstance(entry, GitLogEntry) for entry in log_entries)

    # Basic check for expected content
    first_entry = log_entries[0]
    assert first_entry.commit_hash is not None
    assert first_entry.author_name is not None
    assert first_entry.commit_message is not None

@pytest.mark.parametrize(
    "pygit2_repo", # Use pygit2_repo fixture
    [
        [
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Initial commit",
                "files": {"file1.txt": "hello world"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Second commit",
                "files": {"file2.txt": "another file"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Dev User",
                "author_email": "dev@example.com",
                "message": "Third commit by Dev User",
                "files": {"file1.txt": "hello world again"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
            },
        ]
    ],
    indirect=True,
)
def test_get_log_entries_since_filter(pygit2_repo): # Use pygit2_repo fixture
    repo_path = pygit2_repo
    backend = Pygit2Backend(repo_path=repo_path)

    # Filter for commits since 4 days ago
    since_date = datetime.now(timezone.utc) - timedelta(days=4)
    since_str = since_date.strftime("%Y-%m-%d")

    filtered_log_entries = backend.get_log_entries(since=since_str)

    # Expected commits:
    # - Initial commit (5 days ago, should NOT be included as it's before 'since_date')
    # - Second commit (3 days ago, should be included)
    # - Third commit (1 day ago, should be included)
    # Total 2 commits
    assert len(filtered_log_entries) == 2

    # Assert that all returned commits are after the since_date
    for entry in filtered_log_entries:
        assert entry.commit_date.date() >= since_date.date()

@pytest.mark.parametrize(
    "pygit2_repo",
    [
        [
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Initial commit",
                "files": {"file1.txt": "hello world", "file2.txt": "another file"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Modify file1",
                "files": {"file1.txt": "hello world modified"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Dev User",
                "author_email": "dev@example.com",
                "message": "Modify file2",
                "files": {"file2.txt": "another file modified"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
            },
        ]
    ],
    indirect=True,
)
def test_get_log_entries_path_filter(pygit2_repo):
    repo_path = pygit2_repo
    backend = Pygit2Backend(repo_path=repo_path)

    # Filter for commits affecting file1.txt
    filtered_log_entries = backend.get_log_entries(include_paths=["file1.txt"])

    # Expected commits:
    # - Initial commit (affects file1.txt)
    # - Modify file1 (affects file1.txt)
    assert len(filtered_log_entries) == 2
    assert all(any(fc.file_path == "file1.txt" for fc in entry.file_changes) for entry in filtered_log_entries)

    # Filter for commits affecting file2.txt
    filtered_log_entries = backend.get_log_entries(include_paths=["file2.txt"])

    # Expected commits:
    # - Initial commit (affects file2.txt)
    # - Modify file2 (affects file2.txt)
    assert len(filtered_log_entries) == 2
    assert all(any(fc.file_path == "file2.txt" for fc in entry.file_changes) for entry in filtered_log_entries)

@pytest.mark.parametrize(
    "pygit2_repo",
    [
        [
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Initial commit",
                "files": {"test_file.txt": "line 1\nline 2\nline 3"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Modify test_file.txt",
                "files": {"test_file.txt": "line 1\nMODIFIED line 2\nline 3"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
            },
        ]
    ],
    indirect=True,
)
def test_get_log_entries_file_modifications(pygit2_repo):
    repo_path = pygit2_repo
    backend = Pygit2Backend(repo_path=repo_path)
    log_entries = backend.get_log_entries()

    # We expect 3 commits: initial empty commit, initial file commit, and modification
    assert len(log_entries) == 3

    # The latest commit is the modification
    mod_commit = log_entries[0]
    assert mod_commit.commit_message == "Modify test_file.txt"
    assert len(mod_commit.file_changes) == 1
    file_change = mod_commit.file_changes[0]
    assert file_change.file_path == "test_file.txt"
    assert file_change.additions == 1
    assert file_change.deletions == 1
    assert file_change.change_type == "M"

    # The initial file commit
    initial_file_commit = log_entries[1]
    assert initial_file_commit.commit_message == "Initial commit"
    assert len(initial_file_commit.file_changes) == 1
    file_change = initial_file_commit.file_changes[0]
    assert file_change.file_path == "test_file.txt"
    assert file_change.additions == 3
    assert file_change.deletions == 0
    assert file_change.change_type == "A"

    assert file_change.change_type == "A"

    assert file_change.change_type == "A"

@pytest.mark.parametrize(
    "pygit2_repo",
    [
        [
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Initial commit",
                "files": {"old_name.txt": "content of the file"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Rename old_name.txt to new_name.txt",
                "files": {"new_name.txt": "content of the file"},
                "rename_files": [("old_name.txt", "new_name.txt")],
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
            },
        ]
    ],
    indirect=True,
)
def test_get_log_entries_file_rename(pygit2_repo):
    repo_path = pygit2_repo
    backend = Pygit2Backend(repo_path=repo_path)
    log_entries = backend.get_log_entries()

    assert len(log_entries) == 3

    # The latest commit is the rename
    rename_commit = log_entries[0]
    assert rename_commit.commit_message == "Rename old_name.txt to new_name.txt"
    assert len(rename_commit.file_changes) == 1
    file_change = rename_commit.file_changes[0]
    assert file_change.file_path == "new_name.txt"
    assert file_change.old_file_path == "old_name.txt"
    assert file_change.additions == 0
    assert file_change.deletions == 0
    assert file_change.change_type == "R"

    # The initial file commit
    initial_file_commit = log_entries[1]
    assert initial_file_commit.commit_message == "Initial commit"
    assert len(initial_file_commit.file_changes) == 1
    file_change = initial_file_commit.file_changes[0]
    assert file_change.file_path == "old_name.txt"
    assert file_change.additions == 1
    assert file_change.deletions == 0
    assert file_change.change_type == "A"

    # The very first commit from the fixture
    fixture_initial_commit = log_entries[2]
    assert fixture_initial_commit.commit_message == "Initial commit"
    assert len(fixture_initial_commit.file_changes) == 1
    file_change = fixture_initial_commit.file_changes[0]
    assert file_change.file_path == "initial_file.txt"
    assert file_change.additions == 1
    assert file_change.deletions == 0
    assert file_change.change_type == "A"

@pytest.mark.parametrize(
    "pygit2_repo",
    [
        [
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Initial commit",
                "files": {"file_to_delete.txt": "line 1\nline 2\nline 3"},
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
            },
            {
                "author_name": "Test User",
                "author_email": "test@example.com",
                "message": "Delete file_to_delete.txt",
                "files": {},
                "delete_files": ["file_to_delete.txt"],
                "commit_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
            },
        ]
    ],
    indirect=True,
)
def test_get_log_entries_file_deletion(pygit2_repo):
    repo_path = pygit2_repo
    backend = Pygit2Backend(repo_path=repo_path)
    log_entries = backend.get_log_entries()

    assert len(log_entries) == 3

    # The latest commit is the deletion
    del_commit = log_entries[0]
    assert del_commit.commit_message == "Delete file_to_delete.txt"
    assert len(del_commit.file_changes) == 1
    file_change = del_commit.file_changes[0]
    assert file_change.file_path == "file_to_delete.txt"
    assert file_change.additions == 0
    assert file_change.deletions == 3
    assert file_change.change_type == "D"

    # The initial file commit
    initial_file_commit = log_entries[1]
    assert initial_file_commit.commit_message == "Initial commit"
    assert len(initial_file_commit.file_changes) == 1
    file_change = initial_file_commit.file_changes[0]
    assert file_change.file_path == "file_to_delete.txt"
    assert file_change.additions == 3
    assert file_change.deletions == 0
    assert file_change.change_type == "A"

    # The very first commit from the fixture
    fixture_initial_commit = log_entries[2]
    assert fixture_initial_commit.commit_message == "Initial commit"
    assert len(fixture_initial_commit.file_changes) == 1
    file_change = fixture_initial_commit.file_changes[0]
    assert file_change.file_path == "initial_file.txt"
    assert file_change.additions == 1
    assert file_change.deletions == 0
    assert file_change.change_type == "A"
