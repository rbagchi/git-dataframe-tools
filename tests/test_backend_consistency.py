import pytest
import subprocess
import os
from tests.conftest import sample_commits
from src.git2df import get_commits_df
from src.git2df.backends import GitCliBackend, GitBackend
from src.git2df.pygit2_backend import Pygit2Backend
from src.git2df.dulwich.backend import DulwichRemoteBackend
from git2df.git_parser import GitLogEntry


def commit_to_dict(commit: GitLogEntry):
    return {
        "parent_hash": commit.parent_hash,
        "author_name": commit.author_name,
        "author_email": commit.author_email,
        "commit_message": commit.commit_message,
        "commit_timestamp": commit.commit_timestamp,
        "file_changes": sorted([
            {
                "file_path": f.file_path,
                "additions": f.additions,
                "deletions": f.deletions,
                "change_type": f.change_type,
                "old_file_path": f.old_file_path,
            } for f in commit.file_changes
        ], key=lambda x: x["file_path"]),
    }


@pytest.fixture(params=[GitCliBackend, Pygit2Backend, DulwichRemoteBackend])
def backend_instance(request, git_repo, remote_git_repo):
    backend_class = request.param
    if backend_class == DulwichRemoteBackend:
        return backend_class(remote_url=remote_git_repo)
    return backend_class(repo_path=git_repo)


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_backend_consistency_basic(git_repo, backend_instance):
    """Test that all backends return the same basic commit data."""
    os.chdir(git_repo)

    # Get commits using the backend instance
    commits = backend_instance.get_log_entries(
        since=None,
        until=None,
        author=None,
        grep=None,
        merged_only=False,
        include_paths=None,
        exclude_paths=None,
    )

    # For now, just assert that we get some commits and the count is correct
    # We will add more detailed comparison later
    assert len(commits) == 4
    assert all(isinstance(c, GitLogEntry) for c in commits)

    # Store results from the first backend for comparison
    if not hasattr(test_backend_consistency_basic, 'expected_commits'):
        test_backend_consistency_basic.expected_commits = sorted([commit_to_dict(c) for c in commits], key=lambda x: (x["commit_timestamp"], x["parent_hash"] or ''))
    else:
        actual_commits = sorted([commit_to_dict(c) for c in commits], key=lambda x: (x["commit_timestamp"], x["parent_hash"] or ''))
        
        # Compare commits with tolerance for timestamp
        assert len(actual_commits) == len(test_backend_consistency_basic.expected_commits)
        for i in range(len(actual_commits)):
            if not compare_commit_dicts(actual_commits[i], test_backend_consistency_basic.expected_commits[i]):
                print("DEBUG: Expected commit:")
                print(test_backend_consistency_basic.expected_commits[i])
                print("DEBUG: Actual commit:")
                print(actual_commits[i])
                assert False, "Commit dictionaries do not match with tolerance."


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
@pytest.mark.parametrize("filter_args", [
    {"since": "1 day ago"},
    {"author": "Test User"},
    {"grep": "Second commit"},
    {"include_paths": ["file1.txt"]},
    {"exclude_paths": ["file2.txt"]},
    {"since": "2 days ago", "author": "Test User", "include_paths": ["file1.txt"]},
])
def test_backend_consistency_with_filters(git_repo, backend_instance, filter_args):
    """Test that all backends return the same commit data with various filters."""
    os.chdir(git_repo)

    # Get commits using the backend instance with filters
    commits = backend_instance.get_log_entries(
        since=filter_args.get("since"),
        until=filter_args.get("until"),
        author=filter_args.get("author"),
        grep=filter_args.get("grep"),
        merged_only=filter_args.get("merged_only", False),
        include_paths=filter_args.get("include_paths"),
        exclude_paths=filter_args.get("exclude_paths"),
    )

    # Store results from the first backend for comparison
    test_id = str(filter_args)
    if not hasattr(test_backend_consistency_with_filters, 'expected_commits'):
        test_backend_consistency_with_filters.expected_commits = {}
    
    if test_id not in test_backend_consistency_with_filters.expected_commits:
        test_backend_consistency_with_filters.expected_commits[test_id] = sorted([commit_to_dict(c) for c in commits], key=lambda x: (x["commit_timestamp"], x["parent_hash"] or ''))
    else:
        actual_commits = sorted([commit_to_dict(c) for c in commits], key=lambda x: (x["commit_timestamp"], x["parent_hash"] or ''))
        expected_commits = test_backend_consistency_with_filters.expected_commits[test_id]
        assert len(actual_commits) == len(expected_commits)
        for i in range(len(actual_commits)):
            if not compare_commit_dicts(actual_commits[i], expected_commits[i]):
                print(f"DEBUG: Filter args: {filter_args}")
                print("DEBUG: Expected commit:")
                print(expected_commits[i])
                print("DEBUG: Actual commit:")
                print(actual_commits[i])
                assert False, "Commit dictionaries do not match with tolerance."

def compare_commit_dicts(dict1: dict, dict2: dict, tolerance_seconds: int = 2) -> bool:
    """Compares two commit dictionaries, allowing for a tolerance in commit_timestamp."""
    if dict1.keys() != dict2.keys():
        return False

    for key in dict1.keys():
        if key == "commit_timestamp":
            if abs(dict1[key] - dict2[key]) > tolerance_seconds:
                print(f"DEBUG: Timestamp mismatch: {dict1[key]} vs {dict2[key]}, diff: {abs(dict1[key] - dict2[key])}")
                return False
        elif key == "file_changes":
            # Compare file_changes list of dictionaries
            if len(dict1[key]) != len(dict2[key]):
                return False
            for fc1, fc2 in zip(dict1[key], dict2[key]):
                if fc1 != fc2:
                    return False
        elif key in ["commit_hash", "parent_hash"]:
            # Ignore commit_hash and parent_hash for direct comparison due to potential differences between backends
            pass
        elif key == "commit_message":
            if dict1[key].strip() != dict2[key].strip():
                print(f"DEBUG: Mismatch in key '{key}': Expected '{dict1[key]}', Actual '{dict2[key]}'")
                return False
        else:
            if dict1[key] != dict2[key]:
                print(f"DEBUG: Mismatch in key '{key}': Expected '{dict1[key]}', Actual '{dict2[key]}'")
                return False
    return True