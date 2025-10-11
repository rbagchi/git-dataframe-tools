from unittest.mock import patch, MagicMock
from git2df.backends import GitCliBackend


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_no_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.return_value = MagicMock(
        stdout=(
            "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
            "10\\t5\\tfile1.txt"
        )
    )

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)

    # Act
    output = backend.get_raw_log_output()

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
        "10\\t5\\tfile1.txt"
    )
    assert output == expected_output
    mock_subprocess_run.assert_called_once()  # Ensure subprocess.run was called
    # Verify the arguments passed to subprocess.run
    args, kwargs = mock_subprocess_run.call_args
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args[0]
    )
    assert "--date=iso-strict" in args[0]
    assert kwargs["cwd"] == repo_path
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is True
    assert kwargs["encoding"] == "utf-8"


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.return_value = MagicMock(stdout=b"")

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    since = "2023-01-01"
    until = "2023-01-31"
    author = "test_author"
    grep = "test_grep"

    # Act
    backend.get_raw_log_output(since=since, until=until, author=author, grep=grep)

    # Assert
    mock_subprocess_run.assert_called_once()
    args, kwargs = mock_subprocess_run.call_args
    assert args[0][0] == "git"
    assert "--numstat" in args[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args[0]
    )
    assert "--date=iso-strict" in args[0]
    assert "--since" in args[0]
    assert since in args[0]
    assert "--until" in args[0]
    assert until in args[0]
    assert "--author" in args[0]
    assert author in args[0]
    assert "--grep" in args[0]
    assert grep in args[0]
    assert kwargs["cwd"] == repo_path
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is True
    assert kwargs["encoding"] == "utf-8"


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_merges(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.return_value = MagicMock(stdout=b"")

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)

    # Act
    backend.get_raw_log_output(merged_only=True)

    # Assert
    mock_subprocess_run.assert_called_once()
    args, kwargs = mock_subprocess_run.call_args
    assert args[0][0] == "git"
    assert "--numstat" in args[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args[0]
    )
    assert "--date=iso-strict" in args[0]
    assert f"origin/{mock_get_default_branch.return_value}" in args[0]
    assert kwargs["cwd"] == repo_path
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is True
    assert kwargs["encoding"] == "utf-8"


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_paths(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.return_value = MagicMock(stdout=b"")

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    include_paths = ["src/"]

    # Act
    backend.get_raw_log_output(include_paths=include_paths)

    # Assert
    mock_subprocess_run.assert_called_once()
    args, kwargs = mock_subprocess_run.call_args
    assert args[0][0] == "git"
    assert "--numstat" in args[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args[0]
    )
    assert "--date=iso-strict" in args[0]
    assert "--" in args[0]
    assert include_paths[0] in args[0]
    assert kwargs["cwd"] == repo_path
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is True
    assert kwargs["encoding"] == "utf-8"


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_exclude_paths(
    mock_subprocess_run, mock_get_default_branch
):
    # Arrange
    mock_subprocess_run.return_value = MagicMock(
        stdout=(
            "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
            "10\\t0\\tsrc/main.py\\n"
            "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T10:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---\n"
            "20\\t0\\ttests/test_main.py"
        )
    )

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    exclude_paths = ["tests/"]

    # Act
    output = backend.get_raw_log_output(exclude_paths=exclude_paths)

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
        "10\\t0\\tsrc/main.py\\n"
        "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T10:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---\n"
        "20\\t0\\ttests/test_main.py"
    )
    assert output == expected_output
    mock_subprocess_run.assert_called_once()
    args, kwargs = mock_subprocess_run.call_args
    assert args[0][0] == "git"
    assert "--numstat" in args[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args[0]
    )
    assert "--date=iso-strict" in args[0]
    assert "--" in args[0]
    assert f":(exclude){exclude_paths[0]}" in args[0]
    assert kwargs["cwd"] == repo_path
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is True
    assert kwargs["encoding"] == "utf-8"
