import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
import pygit2
from .git_helpers import _handle_file_changes, _handle_file_deletions, _handle_file_renames, _create_merge_commit

@pytest.fixture
def pygit2_repo(request):
    """
    A pytest fixture that creates a temporary Git repository for testing using pygit2.
    Can be pre-populated with commits using `request.param`.
    The `request.param` should be a list of commit data dictionaries.
    Each dictionary can optionally include a 'commit_date' field (datetime object).
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path, exist_ok=True)
        try:
            os.chdir(repo_path)

            # Initialize pygit2 repository
            repo = pygit2.init_repository(repo_path)

            # Set up default user
            author_name = "Default User"
            author_email = "default@example.com"

            # Initial commit
            initial_file_path = Path(repo_path) / "initial_file.txt"
            initial_file_path.write_text("initial content")
            repo.index.add("initial_file.txt")
            repo.index.write()
            tree = repo.index.write_tree()

            initial_commit_date = "2023-01-01T09:00:00Z"
            initial_commit_timestamp = int(datetime.fromisoformat(initial_commit_date.replace('Z', '+00:00')).timestamp())
            initial_author = pygit2.Signature(author_name, author_email, initial_commit_timestamp, 0)
            initial_committer = pygit2.Signature(author_name, author_email, initial_commit_timestamp, 0)

            initial_commit_oid = repo.create_commit(
                "HEAD", # Commit to HEAD first
                initial_author,
                initial_committer,
                "Initial commit",
                tree,
                [],
            )
            # Create 'main' branch and set HEAD to it
            repo.create_branch("main", repo.get(initial_commit_oid))
            repo.head.set_target(repo.lookup_reference("refs/heads/main").target)

            # Process parameterized commits
            if hasattr(request, "param") and isinstance(request.param, list):
                for commit_data in request.param:
                    # Set up user for commit
                    current_author_name = commit_data.get("author_name", author_name)
                    current_author_email = commit_data.get("author_email", author_email)
                    
                    # Ensure commit_timestamp is derived from fixed commit_date
                    commit_date_obj = datetime.fromisoformat(commit_data["commit_date"].replace('Z', '+00:00'))
                    commit_timestamp = int(commit_date_obj.timestamp())

                    current_author = pygit2.Signature(current_author_name, current_author_email, commit_timestamp, 0)
                    current_committer = pygit2.Signature(current_author_name, current_author_email, commit_timestamp, 0)

                    _handle_file_changes(repo, repo_path, commit_data)
                    _handle_file_deletions(repo, repo_path, commit_data)
                    _handle_file_renames(repo, repo_path, commit_data)

                    if "merge_branch" in commit_data:
                        _create_merge_commit(repo, current_author, current_committer, commit_data, repo_path)
                    else:
                        repo.index.write()
                        tree = repo.index.write_tree()

                        parent_commit_oid = repo.lookup_reference("refs/heads/main").target

                        new_commit_oid = repo.create_commit(
                            "refs/heads/main",
                            current_author,
                            current_committer,
                            commit_data["message"],
                            tree,
                            [parent_commit_oid],
                        )
                        repo.head.set_target(new_commit_oid)
            yield repo_path
        finally:
            os.chdir(original_cwd)
