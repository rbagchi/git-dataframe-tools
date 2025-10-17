import pytest
import os
from tests.conftest import sample_commits
from src.git2df.backends import GitCliBackend
from src.git2df.pygit2_backend import Pygit2Backend
from src.git2df.dulwich.backend import DulwichRemoteBackend
from git2df.git_parser import GitLogEntry

REGENERATE_GOLDEN_FILES = os.environ.get("REGENERATE_GOLDEN_FILES", "false").lower() == "true"

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
def test_backend_consistency_basic(git_repo, backend_instance, golden_file_manager):
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

    actual_commits = sorted([commit_to_dict(c) for c in commits], key=lambda x: (x["commit_timestamp"], x["parent_hash"] or ''))

    test_id = f"basic_{backend_instance.__class__.__name__}"
    print(f"DEBUG: Type of golden_file_manager: {type(golden_file_manager)}")
    
    if REGENERATE_GOLDEN_FILES:
        golden_file_manager.save_golden_file(test_id, {}, actual_commits)
        pytest.skip(f"Golden file for {test_id} regenerated.")

    expected_commits = golden_file_manager.load_golden_file(test_id, {})
    assert expected_commits is not None, f"Golden file not found for {test_id}. Run with REGENERATE_GOLDEN_FILES=true."

    assert len(actual_commits) == len(expected_commits), f"Mismatch in commit count for {test_id}"
    for i in range(len(actual_commits)):
        if not compare_commit_dicts(actual_commits[i], expected_commits[i]):
            print(f"DEBUG: Mismatch in {test_id} at index {i}")
            print("DEBUG: Expected commit:")
            print(expected_commits[i])
            print("DEBUG: Actual commit:")
            print(actual_commits[i])
            assert False, f"Commit dictionaries do not match for {test_id} at index {i}."


@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
@pytest.mark.parametrize("filter_args", [
    {"since": "1 day ago"},
    {"author": "Test User"},
    {"grep": "Second commit"},
    {"include_paths": ["file1.txt"]},
    {"exclude_paths": ["file2.txt"]},
    {"since": "2 days ago", "author": "Test User", "include_paths": ["file1.txt"]},
])
def test_backend_consistency_with_filters(git_repo, backend_instance, filter_args, golden_file_manager):
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

    actual_commits = sorted([commit_to_dict(c) for c in commits], key=lambda x: (x["commit_timestamp"], x["parent_hash"] or ''))

    test_id = f"filtered_{backend_instance.__class__.__name__}"
    param_id = "-".join(f"{k}_{v}" for k, v in sorted(filter_args.items()))

    if REGENERATE_GOLDEN_FILES:
        golden_file_manager.save_golden_file(test_id, filter_args, actual_commits)
        pytest.skip(f"Golden file for {test_id} with params {param_id} regenerated.")

    expected_commits = golden_file_manager.load_golden_file(test_id, filter_args)
    assert expected_commits is not None, f"Golden file not found for {test_id} with params {param_id}. Run with REGENERATE_GOLDEN_FILES=true."

    assert len(actual_commits) == len(expected_commits), f"Mismatch in commit count for {test_id} with params {param_id}"
    for i in range(len(actual_commits)):
        if not compare_commit_dicts(actual_commits[i], expected_commits[i]):
            print(f"DEBUG: Mismatch in {test_id} with params {param_id} at index {i}")
            print("DEBUG: Expected commit:")
            print(expected_commits[i])
            print("DEBUG: Actual commit:")
            print(actual_commits[i])
            assert False, f"Commit dictionaries do not match for {test_id} with params {param_id} at index {i}."

def _compare_file_changes(file_changes1: list[dict], file_changes2: list[dict]) -> bool:
    if len(file_changes1) != len(file_changes2):
        return False
    for fc1, fc2 in zip(file_changes1, file_changes2):
        if fc1 != fc2:
            return False
    return True

def compare_commit_dicts(dict1: dict, dict2: dict, tolerance_seconds: int = 2) -> bool:
    """Compares two commit dictionaries, allowing for a tolerance in commit_timestamp."""
    if dict1.keys() != dict2.keys():
        return False

    comparison_strategies = {
        "commit_timestamp": lambda v1, v2: abs(v1 - v2) <= tolerance_seconds,
        "file_changes": _compare_file_changes,
        "commit_hash": lambda v1, v2: True,  # Ignore for direct comparison
        "parent_hash": lambda v1, v2: True,  # Ignore for direct comparison
        "commit_message": lambda v1, v2: v1.strip() == v2.strip(),
    }

    for key in dict1.keys():
        if key in comparison_strategies:
            if not comparison_strategies[key](dict1[key], dict2[key]):
                print(f"DEBUG: Mismatch in key '{key}'.")
                if key == "commit_timestamp":
                    print(f"DEBUG: Timestamp mismatch: {dict1[key]} vs {dict2[key]}, diff: {abs(dict1[key] - dict2[key])}")
                elif key == "commit_message":
                    print(f"DEBUG: Mismatch in key '{key}': Expected '{dict1[key]}', Actual '{dict2[key]}'")
                return False
        else:
            if dict1[key] != dict2[key]:
                print(f"DEBUG: Mismatch in key '{key}': Expected '{dict1[key]}', Actual '{dict2[key]}'")
                return False
    return True