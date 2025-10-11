from unittest.mock import MagicMock, patch
from typing import Optional

import pytest
from dulwich.objects import Commit, Blob, TreeEntry
from dulwich.repo import Repo
from dulwich.diff_tree import TreeChange

from git2df.dulwich.diff_parser import DulwichDiffParser


# Helper to create a mock blob object
def create_mock_blob(sha: bytes, content: str) -> MagicMock:
    mock_blob = MagicMock(spec=Blob)
    mock_blob.id = sha
    mock_blob.as_pretty_string.return_value = content
    return mock_blob


# Helper to create a mock TreeChange object
def create_mock_tree_change(
    type: str,
    old_path: Optional[bytes] = None,
    new_path: Optional[bytes] = None,
    old_sha: Optional[bytes] = b"0" * 20,
    new_sha: Optional[bytes] = b"0" * 20,
) -> TreeChange:
    old = None
    if old_path:
        old = TreeEntry(path=old_path, mode=0o100644, sha=old_sha or b"0" * 20)

    new = None
    if new_path:
        new = TreeEntry(path=new_path, mode=0o100644, sha=new_sha or b"0" * 20)

    return TreeChange(type=type, old=old, new=new)


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=Repo)
    repo.object_store = MagicMock()
    return repo


@pytest.fixture
def mock_commit():
    commit = MagicMock(spec=Commit)
    commit.parents = []  # Assume no parents for simplicity in some tests
    commit.tree = b"new_tree_sha"
    return commit

def test_extract_file_changes_modification(mock_repo, mock_commit):
    # Arrange
    old_tree_id = b"old_tree_sha"
    parser = DulwichDiffParser()

    # Mock dulwich.patch.write_tree_diff output for a modification
    mock_diff_output = (
        b"diff --git a/file.txt b/file.txt\n"
        b"index 1234567..890abcdef 100644\n"
        b"--- a/file.txt\n"
        b"+++ b/file.txt\n"
        b"@@ -1,2 +1,3 @@\n"
        b"-line1\n"
        b"+line1_modified\n"
        b"+line2_added\n"
    ).decode("utf-8")

    with patch("dulwich.patch.write_object_diff") as mock_write_object_diff:
        def side_effect(stream, *args, **kwargs):
            stream.write(mock_diff_output.encode("utf-8"))
        mock_write_object_diff.side_effect = side_effect

        # Mock dulwich.diff_tree.tree_changes to return a modify change
        mock_tree_change = create_mock_tree_change(
            type="modify", old_path=b"file.txt", new_path=b"file.txt"
        )
        with patch("dulwich.diff_tree.tree_changes") as mock_tree_changes:
            mock_tree_changes.return_value = [mock_tree_change]

            # Act
            file_changes = parser.extract_file_changes(mock_repo, mock_commit, old_tree_id)

            # Assert
            assert len(file_changes) == 1
            assert file_changes[0]["file_paths"] == "file.txt"
            assert file_changes[0]["change_type"] == "M"
            assert file_changes[0]["additions"] == 2
            assert file_changes[0]["deletions"] == 1

def test_extract_file_changes_addition(mock_repo, mock_commit):
    # Arrange
    old_tree_id = b"old_tree_sha"
    parser = DulwichDiffParser()

    # Mock dulwich.patch.write_tree_diff output for an addition
    mock_diff_output = (
        b"diff --git a/dev/null b/new_file.txt\n"
        b"new file mode 100644\n"
        b"--- /dev/null\n"
        b"+++ b/new_file.txt\n"
        b"@@ -0,0 +1,2 @@\n"
        b"+line1\n"
        b"+line2\n"
    ).decode("utf-8")

    with patch("dulwich.patch.write_tree_diff") as mock_write_tree_diff:
        def side_effect(stream, *args, **kwargs):
            stream.write(mock_diff_output.encode("utf-8"))
        mock_write_tree_diff.side_effect = side_effect

        # Mock dulwich.diff_tree.tree_changes to return an add change
        mock_tree_change = create_mock_tree_change(
            type="add", new_path=b"new_file.txt", new_sha=b"new_blob_sha"
        )
        mock_repo.get_object.return_value = create_mock_blob(b"new_blob_sha", "line1\nline2")

        with patch("dulwich.diff_tree.tree_changes") as mock_tree_changes:
            mock_tree_changes.return_value = [mock_tree_change]

            # Act
            file_changes = parser.extract_file_changes(mock_repo, mock_commit, old_tree_id)

            # Assert
            assert len(file_changes) == 1
            assert file_changes[0]["file_paths"] == "new_file.txt"
            assert file_changes[0]["change_type"] == "A"
            assert file_changes[0]["additions"] == 2
            assert file_changes[0]["deletions"] == 0

def test_extract_file_changes_deletion(mock_repo, mock_commit):
    # Arrange
    old_tree_id = b"old_tree_sha"
    parser = DulwichDiffParser()

    # Mock dulwich.patch.write_tree_diff output for a deletion
    mock_diff_output = (
        b"diff --git a/old_file.txt b/dev/null\n"
        b"deleted file mode 100644\n"
        b"--- a/old_file.txt\n"
        b"+++ /dev/null\n"
        b"@@ -1,2 +0,0 @@\n"
        b"-line1\n"
        b"-line2\n"
    ).decode("utf-8")

    with patch("dulwich.patch.write_tree_diff") as mock_write_tree_diff:
        def side_effect(stream, *args, **kwargs):
            stream.write(mock_diff_output.encode("utf-8"))
        mock_write_tree_diff.side_effect = side_effect

        # Mock dulwich.diff_tree.tree_changes to return a delete change
        mock_tree_change = create_mock_tree_change(
            type="delete", old_path=b"old_file.txt", old_sha=b"old_blob_sha"
        )
        mock_repo.get_object.return_value = create_mock_blob(b"old_blob_sha", "line1\nline2")

        with patch("dulwich.diff_tree.tree_changes") as mock_tree_changes:
            mock_tree_changes.return_value = [mock_tree_change]

            # Act
            file_changes = parser.extract_file_changes(mock_repo, mock_commit, old_tree_id)

            # Assert
            assert len(file_changes) == 1
            assert file_changes[0]["file_paths"] == "old_file.txt"
            assert file_changes[0]["change_type"] == "D"
            assert file_changes[0]["additions"] == 0
            assert file_changes[0]["deletions"] == 2

def test_extract_file_changes_with_path_include_filter(mock_repo, mock_commit):
    # Arrange
    old_tree_id = b"old_tree_sha"
    parser = DulwichDiffParser(include_paths=["src/"])

    mock_diff_output = (
        b"diff --git a/src/file1.txt b/src/file1.txt\n"
        b"--- a/src/file1.txt\n"
        b"+++ b/src/file1.txt\n"
        b"@@ -1 +1 @@\n"
        b"-old\n"
        b"+new\n"
    ).decode("utf-8")

    with patch("dulwich.patch.write_object_diff") as mock_write_object_diff:
        def side_effect(stream, *args, **kwargs):
            stream.write(mock_diff_output.encode("utf-8"))
        mock_write_object_diff.side_effect = side_effect

        mock_tree_changes_list = [
            create_mock_tree_change(type="modify", old_path=b"src/file1.txt", new_path=b"src/file1.txt"),
            create_mock_tree_change(type="modify", old_path=b"test/file2.txt", new_path=b"test/file2.txt"),
        ]
        with patch("dulwich.diff_tree.tree_changes") as mock_tree_changes:
            mock_tree_changes.return_value = mock_tree_changes_list

            # Act
            file_changes = parser.extract_file_changes(mock_repo, mock_commit, old_tree_id)

            # Assert
            assert len(file_changes) == 1
            assert file_changes[0]["file_paths"] == "src/file1.txt"
            assert file_changes[0]["change_type"] == "M"
            assert file_changes[0]["additions"] == 1
            assert file_changes[0]["deletions"] == 1

def test_extract_file_changes_with_path_exclude_filter(mock_repo, mock_commit):
    # Arrange
    old_tree_id = b"old_tree_sha"
    parser = DulwichDiffParser(exclude_paths=["test/"])

    mock_diff_output = (
        b"diff --git a/src/file1.txt b/src/file1.txt\n"
        b"--- a/src/file1.txt\n"
        b"+++ b/src/file1.txt\n"
        b"@@ -1 +1 @@\n"
        b"-old\n"
        b"+new\n"
    ).decode("utf-8")

    with patch("dulwich.patch.write_object_diff") as mock_write_object_diff:
        def side_effect(stream, *args, **kwargs):
            stream.write(mock_diff_output.encode("utf-8"))
        mock_write_object_diff.side_effect = side_effect

        mock_tree_changes_list = [
            create_mock_tree_change(type="modify", old_path=b"src/file1.txt", new_path=b"src/file1.txt"),
            create_mock_tree_change(type="modify", old_path=b"test/file2.txt", new_path=b"test/file2.txt"),
        ]
        with patch("dulwich.diff_tree.tree_changes") as mock_tree_changes:
            mock_tree_changes.return_value = mock_tree_changes_list

            # Act
            file_changes = parser.extract_file_changes(mock_repo, mock_commit, old_tree_id)

            # Assert
            assert len(file_changes) == 1
            assert file_changes[0]["file_paths"] == "src/file1.txt"
            assert file_changes[0]["change_type"] == "M"
            assert file_changes[0]["additions"] == 1
            assert file_changes[0]["deletions"] == 1

def test_extract_file_changes_empty_diff(mock_repo, mock_commit):
    # Arrange
    old_tree_id = b"old_tree_sha"
    parser = DulwichDiffParser()

    mock_diff_output = b"".decode("utf-8")

    with patch("dulwich.patch.write_tree_diff") as mock_write_tree_diff:
        def side_effect(stream, *args, **kwargs):
            stream.write(mock_diff_output.encode("utf-8"))
        mock_write_tree_diff.side_effect = side_effect

        with patch("dulwich.diff_tree.tree_changes") as mock_tree_changes:
            mock_tree_changes.return_value = []

            # Act
            file_changes = parser.extract_file_changes(mock_repo, mock_commit, old_tree_id)

            # Assert
            assert len(file_changes) == 0
