from unittest.mock import patch, MagicMock
from git2df.backends import GitCliBackend
from datetime import datetime, timezone


@patch("git2df.backends.git.Repo")
@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
def test_get_raw_log_output_no_filters(mock_get_default_branch, mock_repo):
    # Arrange
    mock_commit = MagicMock()
    mock_commit.hexsha = "commit1hash"
    mock_commit.parents = []
    mock_commit.author.name = "Author One"
    mock_commit.author.email = "author1@example.com"
    mock_commit.authored_datetime = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    mock_commit.summary = "Subject 1"
    mock_commit.stats.files = {"file1.txt": {"insertions": 10, "deletions": 5}}

    mock_repo_instance = MagicMock()
    mock_repo_instance.iter_commits.return_value = [mock_commit]
    mock_repo.return_value = mock_repo_instance

    backend = GitCliBackend()
    repo_path = "/test/repo"

    # Act
    output = backend.get_raw_log_output(repo_path)

    # Assert
    expected_output = (
        "---commit1hash------Author One---author1@example.com---2023-01-01T10:00:00+00:00---Subject 1\n"
        "10\t5\tfile1.txt"
    )
    assert output == expected_output
    mock_repo.assert_called_once_with(repo_path)
    mock_repo_instance.iter_commits.assert_called_once_with()


@patch("git2df.backends.git.Repo")
@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
def test_get_raw_log_output_with_filters(mock_get_default_branch, mock_repo):
    # Arrange
    mock_repo_instance = MagicMock()
    mock_repo_instance.iter_commits.return_value = []
    mock_repo.return_value = mock_repo_instance

    backend = GitCliBackend()
    repo_path = "/test/repo"
    since = "2023-01-01"
    until = "2023-01-31"
    author = "test_author"
    grep = "test_grep"

    # Act
    backend.get_raw_log_output(
        repo_path, since=since, until=until, author=author, grep=grep
    )

    # Assert
    mock_repo_instance.iter_commits.assert_called_once_with(
        since=since, until=until, author=author, grep=grep
    )


@patch("git2df.backends.git.Repo")
@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
def test_get_raw_log_output_with_merges(mock_get_default_branch, mock_repo):
    # Arrange
    mock_repo_instance = MagicMock()
    mock_repo_instance.iter_commits.return_value = []
    mock_repo.return_value = mock_repo_instance

    backend = GitCliBackend()
    repo_path = "/test/repo"

    # Act
    backend.get_raw_log_output(repo_path, merged_only=True)

    # Assert
    mock_repo_instance.iter_commits.assert_called_once_with(
        merges=True, rev="origin/main"
    )


@patch("git2df.backends.git.Repo")
@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
def test_get_raw_log_output_with_paths(mock_get_default_branch, mock_repo):
    # Arrange
    mock_repo_instance = MagicMock()
    mock_repo_instance.iter_commits.return_value = []
    mock_repo.return_value = mock_repo_instance

    backend = GitCliBackend()
    repo_path = "/test/repo"
    include_paths = ["src/"]

    # Act
    backend.get_raw_log_output(repo_path, include_paths=include_paths)

    # Assert
    mock_repo_instance.iter_commits.assert_called_once_with(paths=include_paths)


@patch("git2df.backends.git.Repo")
@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
def test_get_raw_log_output_with_exclude_paths(mock_get_default_branch, mock_repo):
    # Arrange
    mock_commit1 = MagicMock()
    mock_commit1.stats.files = {"src/main.py": {"insertions": 10, "deletions": 0}}
    mock_commit2 = MagicMock()
    mock_commit2.stats.files = {
        "tests/test_main.py": {"insertions": 20, "deletions": 0}
    }

    mock_repo_instance = MagicMock()
    mock_repo_instance.iter_commits.return_value = [mock_commit1, mock_commit2]
    mock_repo.return_value = mock_repo_instance

    backend = GitCliBackend()
    repo_path = "/test/repo"
    exclude_paths = ["tests/"]

    # Act
    output = backend.get_raw_log_output(repo_path, exclude_paths=exclude_paths)

    # Assert
    assert "tests/test_main.py" not in output
    assert "src/main.py" in output
