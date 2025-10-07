from unittest.mock import MagicMock
from dulwich.objects import Commit

def test_mock_commit_hex_method():
    sha = "test_sha_123"

    # Mock commit object
    mock_commit = MagicMock(spec=Commit)

    # Mock commit.id (which is bytes) and its hex() method
    mock_commit.id = MagicMock(spec=bytes)
    mock_commit.id.hex.return_value = sha

    # Assertions
    assert mock_commit.id.hex() == sha

def test_mock_parent_commit_hex_method():
    parent_sha = "parent_sha_456"

    # Mock parent commit object
    mock_parent_commit = MagicMock()
    mock_parent_commit.id = MagicMock(spec=bytes)
    mock_parent_commit.id.hex.return_value = parent_sha
    mock_parent_commit.hex.return_value = parent_sha # Mock the hex() method directly

    # Assertions
    assert mock_parent_commit.id.hex() == parent_sha
    assert mock_parent_commit.hex() == parent_sha