# F401 (unused-imports) is ignored in conftest.py because pytest automatically discovers and uses fixtures,
# so explicit usage within conftest.py is not required and would be misleading to linters.
# ruff: noqa: F401
import logging

# This conftest.py is used to make fixtures defined in tests/fixtures/ available to all tests.
# For fixture implementations, please refer to the files in the tests/fixtures/ directory.

# Import fixtures from new modules
from .fixtures.golden_files import golden_file_manager
from .fixtures.sample_data import sample_commits
from .fixtures.markdown_utils import extract_code_blocks
from .fixtures.git_cli_fixtures import git_repo
from .fixtures.pygit2_fixtures import pygit2_repo
from .fixtures.remote_repo_fixtures import remote_git_repo
import os
from datetime import datetime, timedelta, timezone
import pytest

@pytest.fixture
def sample_single_initial_commit():
    return [
        {
            "author_name": "Initial Author",
            "author_email": "initial@example.com",
            "message": "Initial commit with no parents",
            "files": {"first_file.txt": "content"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d"),
        },
    ]

@pytest.fixture
def sample_unusual_character_commits():
    return [
        {
            "author_name": "Jöhn Döe",
            "author_email": "john.doe+test@example.com",
            "message": "Commit with unicode characters: éàçüö",
            "files": {"file_é.txt": "content with é"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
        },
        {
            "author_name": "User <with> special chars",
            "author_email": "user@special.chars.com",
            "message": "Another commit with [brackets] and !exclamations!",
            "files": {"file_!.txt": "content with !"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
        },
    ]

logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def sample_merge_commits():
    return [
        {
            "author_name": "Feature Author",
            "author_email": "feature@example.com",
            "message": "Initial commit on feature branch",
            "files": {"feature_file.txt": "feature content"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"),
            "branch": "feature",
        },
        {
            "author_name": "Main Author",
            "author_email": "main@example.com",
            "message": "Initial commit on main branch",
            "files": {"main_file.txt": "main content"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=8)).strftime("%Y-%m-%d"),
        },
        {
            "author_name": "Main Author",
            "author_email": "main@example.com",
            "message": "Merge feature into main",
            "files": {},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=6)).strftime("%Y-%m-%d"),
            "merge_from": "feature",
        },
    ]

@pytest.fixture
def sample_rename_commits():
    return [
        {
            "author_name": "Rename Author",
            "author_email": "rename@example.com",
            "message": "Initial commit with file to be renamed",
            "files": {"old_name.txt": "content"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d"),
        },
        {
            "author_name": "Rename Author",
            "author_email": "rename@example.com",
            "message": "Rename old_name.txt to new_name.txt",
            "renames": [("old_name.txt", "new_name.txt")],
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
    ]

@pytest.fixture
def sample_multiple_branches_commits():
    return [
        {
            "author_name": "Main Author",
            "author_email": "main@example.com",
            "message": "Initial commit on main",
            "files": {"main_file.txt": "content"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d"),
        },
        {
            "author_name": "Feature Author",
            "author_email": "feature@example.com",
            "message": "First commit on feature branch",
            "files": {"feature_file1.txt": "feature content 1"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=8)).strftime("%Y-%m-%d"),
            "branch": "feature",
        },
        {
            "author_name": "Main Author",
            "author_email": "main@example.com",
            "message": "Second commit on main",
            "files": {"main_file2.txt": "content 2"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"),
        },
        {
            "author_name": "Feature Author",
            "author_email": "feature@example.com",
            "message": "Second commit on feature branch",
            "files": {"feature_file2.txt": "feature content 2"},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=6)).strftime("%Y-%m-%d"),
            "branch": "feature",
        },
    ]
@pytest.fixture
def sample_large_binary_files_commits():
    # Create a large binary file (e.g., 1MB of random bytes)
    large_file_content = os.urandom(1024 * 1024) # 1MB
    return [
        {
            "author_name": "Binary Author",
            "author_email": "binary@example.com",
            "message": "Initial commit with large binary file",
            "files": {"large_binary.bin": large_file_content},
            "commit_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
    ]