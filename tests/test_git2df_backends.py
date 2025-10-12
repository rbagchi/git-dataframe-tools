from unittest.mock import patch, MagicMock
from git2df.backends import GitCliBackend
from typing import List, Any

def _setup_mock_subprocess_run_side_effect(rev_list_stdout: str, metadata_stdout: str, numstat_stdout: str, name_status_stdout: str, num_commits: int = 1) -> List[MagicMock]:
    side_effect = [MagicMock(stdout=rev_list_stdout)]
    for _ in range(num_commits):
        side_effect.extend([
            MagicMock(stdout=metadata_stdout),
            MagicMock(stdout=numstat_stdout),
            MagicMock(stdout=name_status_stdout),
        ])
    return side_effect

def _assert_metadata_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str]) -> None:
    args, kwargs = call_args
    assert args[0][:3] == ["git", "show", commit_hash]
    assert "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---" in args[0]
    assert "--date=iso-strict" in args[0]
    for path_filter in expected_path_filters:
        assert path_filter in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_numstat_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str]) -> None:
    args, kwargs = call_args
    assert args[0][:4] == ["git", "show", commit_hash, "--numstat"]
    for path_filter in expected_path_filters:
        assert path_filter in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_name_status_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str]) -> None:
    args, kwargs = call_args
    assert args[0][:4] == ["git", "show", commit_hash, "--name-status"]
    for path_filter in expected_path_filters:
        assert path_filter in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_subprocess_calls(mock_subprocess_run: MagicMock, repo_path: str, expected_rev_list_args: List[str], expected_path_filters: List[str], num_commits: int = 1) -> None:
    assert mock_subprocess_run.call_count == 1 + (num_commits * 3)

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert args0[0] == ["git", "rev-list", "--all"] + expected_rev_list_args + expected_path_filters
    assert kwargs0["cwd"] == repo_path

    for i in range(num_commits):
        commit_hash = f"commit{i+1}hash"
        _assert_metadata_call(mock_subprocess_run.call_args_list[1 + (i * 3)], commit_hash, repo_path, expected_path_filters)
        _assert_numstat_call(mock_subprocess_run.call_args_list[2 + (i * 3)], commit_hash, repo_path, expected_path_filters)
        _assert_name_status_call(mock_subprocess_run.call_args_list[3 + (i * 3)], commit_hash, repo_path, expected_path_filters)


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_no_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    rev_list_stdout = "commit1hash\n"
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
    numstat_stdout = "10\t5\tfile1.txt\n"
    name_status_stdout = "M\tfile1.txt\n"
    mock_subprocess_run.side_effect = _setup_mock_subprocess_run_side_effect(rev_list_stdout, metadata_stdout, numstat_stdout, name_status_stdout)

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)

    # Act
    output = backend.get_raw_log_output()
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
        "10\t5\tM\tfile1.txt"
    )
    assert output == expected_output
    _assert_subprocess_calls(mock_subprocess_run, repo_path, [], [])


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    rev_list_stdout = "commit1hash\n"
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
    numstat_stdout = "10\t5\tfile1.txt\n"
    name_status_stdout = "M\tfile1.txt\n"
    mock_subprocess_run.side_effect = _setup_mock_subprocess_run_side_effect(rev_list_stdout, metadata_stdout, numstat_stdout, name_status_stdout)

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    since = "2023-01-01"
    until = "2023-01-31"
    author = "test_author"
    grep = "test_grep"

    # Act
    output = backend.get_raw_log_output(
        since=since, until=until, author=author, grep=grep
    )

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
        "10\t5\tM\tfile1.txt"
    )
    assert output == expected_output
    expected_rev_list_args = [
        "--since", since, "--until", until, "--author", author, "--grep", grep
    ]
    _assert_subprocess_calls(mock_subprocess_run, repo_path, expected_rev_list_args, [])


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_merges(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    rev_list_stdout = "commit1hash\n"
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Merge commit---MSG_END---\n"
    numstat_stdout = "10\t5\tfile1.txt\n"
    name_status_stdout = "M\tfile1.txt\n"
    mock_subprocess_run.side_effect = _setup_mock_subprocess_run_side_effect(rev_list_stdout, metadata_stdout, numstat_stdout, name_status_stdout)

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)

    # Act
    output = backend.get_raw_log_output(merged_only=True)

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Merge commit---MSG_END---\n"
        "10\t5\tM\tfile1.txt"
    )
    assert output == expected_output
    expected_rev_list_args = ["--merges", f"origin/{mock_get_default_branch.return_value}"]
    _assert_subprocess_calls(mock_subprocess_run, repo_path, expected_rev_list_args, [])


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_paths(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    rev_list_stdout = "commit1hash\n"
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
    numstat_stdout = "10\t5\tsrc/file1.txt\n"
    name_status_stdout = "M\tsrc/file1.txt\n"
    mock_subprocess_run.side_effect = _setup_mock_subprocess_run_side_effect(rev_list_stdout, metadata_stdout, numstat_stdout, name_status_stdout)

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    include_paths = ["src/"]

    # Act
    output = backend.get_raw_log_output(include_paths=include_paths)

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
        "10\t5\tM\tsrc/file1.txt"
    )
    assert output == expected_output
    expected_rev_list_args = ["--"] + include_paths
    _assert_subprocess_calls(mock_subprocess_run, repo_path, expected_rev_list_args, include_paths)


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_exclude_paths(
    mock_subprocess_run, mock_get_default_branch
):
    # Arrange
    mock_subprocess_run.side_effect = [
        # 1. git rev-list output
        MagicMock(stdout="commit1hash\ncommit2hash\n"),
        # For commit1hash
        # 2. git show for metadata
        MagicMock(
            stdout=(
                "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
            )
        ),
        # 3. git show for numstat
        MagicMock(stdout="10\t0\tsrc/main.py\n"),
        # 4. git show for name-status
        MagicMock(stdout="M\tsrc/main.py\n"),
        # For commit2hash
        # 5. git show for metadata
        MagicMock(
            stdout=(
                "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T10:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---\n"
            )
        ),
        # 6. git show for numstat
        MagicMock(stdout="20\t0\ttests/test_main.py\n"),
        # 7. git show for name-status
        MagicMock(stdout="M\ttests/test_main.py\n"),
    ]

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    exclude_paths = ["tests/"]

    # Act
    output = backend.get_raw_log_output(exclude_paths=exclude_paths)

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
        "10\t0\tM\tsrc/main.py\n"
        "@@@COMMIT@@@commit2hash@@@FIELD@@@@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T10:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---\n"
        "20\t0\tM\ttests/test_main.py"
    )
    assert output == expected_output
    assert mock_subprocess_run.call_count == 7

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert "rev-list" in args0[0]
    assert "--all" in args0[0]
    assert "--" in args0[0]
    assert f":(exclude){exclude_paths[0]}" in args0[0]
    assert kwargs0["cwd"] == repo_path

    # Assertions for the second call (metadata for commit1hash)
    args1, kwargs1 = mock_subprocess_run.call_args_list[1]
    assert "show" in args1[0]
    assert "commit1hash" in args1[0]
    assert "--numstat" not in args1[0]
    assert "--name-status" not in args1[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args1[0]
    )
    assert "--" in args1[0]
    assert f":(exclude){exclude_paths[0]}" in args1[0]
    assert kwargs1["cwd"] == repo_path

    # Assertions for the third call (numstat for commit1hash)
    args2, kwargs2 = mock_subprocess_run.call_args_list[2]
    assert "show" in args2[0]
    assert "commit1hash" in args2[0]
    assert "--numstat" in args2[0]
    assert "--name-status" not in args2[0]
    assert "--" in args2[0]
    assert f":(exclude){exclude_paths[0]}" in args2[0]
    assert kwargs2["cwd"] == repo_path

    # Assertions for the fourth call (name-status for commit1hash)
    args3, kwargs3 = mock_subprocess_run.call_args_list[3]
    assert "show" in args3[0]
    assert "commit1hash" in args3[0]
    assert "--name-status" in args3[0]
    assert "--numstat" not in args3[0]
    assert "--" in args3[0]
    assert f":(exclude){exclude_paths[0]}" in args3[0]
    assert kwargs3["cwd"] == repo_path

    # Assertions for the fifth call (metadata for commit2hash)
    args4, kwargs4 = mock_subprocess_run.call_args_list[4]
    assert "show" in args4[0]
    assert "commit2hash" in args4[0]
    assert "--numstat" not in args4[0]
    assert "--name-status" not in args4[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args4[0]
    )
    assert "--" in args4[0]
    assert f":(exclude){exclude_paths[0]}" in args4[0]
    assert kwargs4["cwd"] == repo_path

    # Assertions for the sixth call (numstat for commit2hash)
    args5, kwargs5 = mock_subprocess_run.call_args_list[5]
    assert "show" in args5[0]
    assert "commit2hash" in args5[0]
    assert "--numstat" in args5[0]
    assert "--name-status" not in args5[0]
    assert "--" in args5[0]
    assert f":(exclude){exclude_paths[0]}" in args5[0]
    assert kwargs5["cwd"] == repo_path

    # Assertions for the seventh call (name-status for commit2hash)
    args6, kwargs6 = mock_subprocess_run.call_args_list[6]
    assert "show" in args6[0]
    assert "commit2hash" in args6[0]
    assert "--name-status" in args6[0]
    assert "--numstat" not in args6[0]
    assert "--" in args6[0]
    assert f":(exclude){exclude_paths[0]}" in args6[0]
    assert kwargs6["cwd"] == repo_path
