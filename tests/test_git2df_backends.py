from unittest.mock import patch, MagicMock
from git2df.backends import GitCliBackend
from typing import List, Any

def _format_path_filters_for_assertion(raw_path_filters: List[str], is_exclude_test: bool = False) -> List[str]:
    """
    Formats raw path filters for assertion in git commands.
    Adds ':(exclude)' prefix for exclude paths if is_exclude_test is True.
    Adds '--' separator if there are path filters.
    """
    formatted_filters = []
    if raw_path_filters:
        formatted_filters.append("--")
        for p in raw_path_filters:
            if is_exclude_test and not p.startswith(":("):
                formatted_filters.append(f":(exclude){p}")
            else:
                formatted_filters.append(p)
    return formatted_filters

def _setup_mock_subprocess_run_side_effect(rev_list_stdout: str, metadata_stdout: str, numstat_stdout: str, name_status_stdout: str, num_commits: int = 1) -> List[MagicMock]:
    side_effect = [MagicMock(stdout=rev_list_stdout)]
    for _ in range(num_commits):
        side_effect.extend([
            MagicMock(stdout=metadata_stdout),
            MagicMock(stdout=numstat_stdout),
            MagicMock(stdout=name_status_stdout),
        ])
    return side_effect

def _assert_metadata_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str], is_exclude_test: bool) -> None:
    args, kwargs = call_args
    assert args[0][:4] == ["git", "show", commit_hash, "--no-patch"]
    assert "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%s---MSG_END---" in args[0]
    assert "--date=iso-strict" in args[0]
    # Construct the expected path filter arguments
    expected_filter_args = _format_path_filters_for_assertion(expected_path_filters, is_exclude_test=is_exclude_test)

    # Assert that the constructed filter arguments are present in the call
    for filter_arg in expected_filter_args:
        assert filter_arg in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_numstat_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str], is_exclude_test: bool) -> None:
    args, kwargs = call_args
    assert args[0][:5] == ["git", "diff-tree", "-r", "--numstat", commit_hash]
    # Construct the expected path filter arguments
    expected_filter_args = _format_path_filters_for_assertion(expected_path_filters, is_exclude_test=is_exclude_test)

    for filter_arg in expected_filter_args:
        assert filter_arg in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_name_status_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str], is_exclude_test: bool) -> None:
    args, kwargs = call_args
    assert args[0][:5] == ["git", "diff-tree", "-r", "--name-status", commit_hash]
    # Construct the expected path filter arguments
    expected_filter_args = _format_path_filters_for_assertion(expected_path_filters, is_exclude_test=is_exclude_test)

    for filter_arg in expected_filter_args:
        assert filter_arg in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_git_show_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str], expected_flags: List[str]) -> None:
    args, kwargs = call_args
    assert args[0][0] == "git"
    assert args[0][1] == "show"
    assert args[0][2] == commit_hash
    for flag in expected_flags:
        assert flag in args[0]
    # Construct the expected path filter arguments
    expected_filter_args = _format_path_filters_for_assertion(expected_path_filters, is_exclude_test=True)

    for filter_arg in expected_filter_args:
        assert filter_arg in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_git_diff_tree_numstat_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str]) -> None:
    args, kwargs = call_args
    # Construct the expected path filter arguments for assertion
    expected_filter_args = _format_path_filters_for_assertion(expected_path_filters, is_exclude_test=True)

    for filter_arg in expected_filter_args:
        assert filter_arg in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_git_diff_tree_name_status_call(call_args: Any, commit_hash: str, repo_path: str, expected_path_filters: List[str]) -> None:
    args, kwargs = call_args
    assert args[0][:5] == ["git", "diff-tree", "-r", "--name-status", commit_hash]
    # Construct the expected path filter arguments for assertion
    expected_filter_args = _format_path_filters_for_assertion(expected_path_filters, is_exclude_test=True)

    for filter_arg in expected_filter_args:
        assert filter_arg in args[0]
    assert kwargs["cwd"] == repo_path

def _assert_subprocess_calls(mock_subprocess_run: MagicMock, repo_path: str, expected_rev_list_args: List[str], expected_path_filters_raw: List[str], num_commits: int = 1) -> None:
    assert mock_subprocess_run.call_count == 1 + (num_commits * 3)

    # Construct the expected rev-list command arguments
    is_exclude = any(":(" in p for p in expected_path_filters_raw)
    full_rev_list_args = ["git", "rev-list", "--all"] + expected_rev_list_args + _format_path_filters_for_assertion(expected_path_filters_raw, is_exclude_test=is_exclude)

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert args0[0] == full_rev_list_args
    assert kwargs0["cwd"] == repo_path
    assert kwargs0["capture_output"] is True
    assert kwargs0["text"] is True
    assert kwargs0["check"] is True
    assert kwargs0["encoding"] == "utf-8"

    for i in range(num_commits):
        commit_hash = f"commit{i+1}hash"
        _assert_metadata_call(mock_subprocess_run.call_args_list[1 + (i * 3)], commit_hash, repo_path, expected_path_filters_raw, is_exclude_test=is_exclude)
        _assert_numstat_call(mock_subprocess_run.call_args_list[2 + (i * 3)], commit_hash, repo_path, expected_path_filters_raw, is_exclude_test=is_exclude)
        _assert_name_status_call(mock_subprocess_run.call_args_list[3 + (i * 3)], commit_hash, repo_path, expected_path_filters_raw, is_exclude_test=is_exclude)


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_no_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    rev_list_stdout = "commit1hash\n"
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
    numstat_stdout = "10\t5\tfile1.txt\n"
    name_status_stdout = "M\tfile1.txt\n"
    mock_subprocess_run.side_effect = _setup_mock_subprocess_run_side_effect(rev_list_stdout, metadata_stdout, numstat_stdout, name_status_stdout)

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)

    # Act
    output = backend.get_raw_log_output()
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
        "\n10\t5\tM\tfile1.txt"
    )
    assert output == expected_output
    _assert_subprocess_calls(mock_subprocess_run, repo_path, [], [])


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    rev_list_stdout = "commit1hash\n"
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
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
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
        "\n10\t5\tM\tfile1.txt"
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
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Merge commit---MSG_END---"
    numstat_stdout = "10\t5\tfile1.txt\n"
    name_status_stdout = "M\tfile1.txt\n"
    mock_subprocess_run.side_effect = _setup_mock_subprocess_run_side_effect(rev_list_stdout, metadata_stdout, numstat_stdout, name_status_stdout)

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)

    # Act
    output = backend.get_raw_log_output(merged_only=True)

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Merge commit---MSG_END---"
        "\n10\t5\tM\tfile1.txt"
    )
    assert output == expected_output
    expected_rev_list_args = ["--merges", f"origin/{mock_get_default_branch.return_value}"]
    _assert_subprocess_calls(mock_subprocess_run, repo_path, expected_rev_list_args, [])


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_paths(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    rev_list_stdout = "commit1hash\n"
    metadata_stdout = "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
    numstat_stdout = "commit1hash\n10\t5\tsrc/file1.txt\n"
    name_status_stdout = "commit1hash\nM\tsrc/file1.txt\n"
    mock_subprocess_run.side_effect = _setup_mock_subprocess_run_side_effect(rev_list_stdout, metadata_stdout, numstat_stdout, name_status_stdout)

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    include_paths = ["src/"]

    # Act
    output = backend.get_raw_log_output(include_paths=include_paths)

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
        "\n10\t5\tM\tsrc/file1.txt"
    )
    assert output == expected_output
    expected_rev_list_args = []
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
                "@@@COMMIT@@@commit1hash@@@FIELD@@@parenthash1@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
            )
        ),
        # 3. git diff-tree for numstat
        MagicMock(stdout="commit1hash\n10\t0\tsrc/main.py\n"),
        # 4. git diff-tree for name-status
        MagicMock(stdout="commit1hash\nM\tsrc/main.py\n"),
        # For commit2hash
        # 5. git show for metadata
        MagicMock(
            stdout=(
                "@@@COMMIT@@@commit2hash@@@FIELD@@@parenthash2@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T10:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---"
            )
        ),
        # 6. git diff-tree for numstat
        MagicMock(stdout="commit2hash\n20\t0\ttests/test_main.py\n"),
        # 7. git diff-tree for name-status
        MagicMock(stdout="commit2hash\nM\ttests/test_main.py\n"),
    ]

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)
    exclude_paths = ["tests/"]

    # Act
    output = backend.get_raw_log_output(exclude_paths=exclude_paths)

    # Assert
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@parenthash1@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---"
        "\n10\t0\tM\tsrc/main.py\n"
        "@@@COMMIT@@@commit2hash@@@FIELD@@@parenthash2@@@FIELD@@@Author Two@@@FIELD@@@author2@example.com@@@FIELD@@@2023-01-02T10:00:00+00:00\t1672617600@@@FIELD@@@---MSG_START---Subject 2---MSG_END---"
        "\n20\t0\tM\ttests/test_main.py"
    )
    assert output == expected_output
    assert mock_subprocess_run.call_count == 7

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert "rev-list" in args0[0] # Corrected from "rev-.venv/lib/python3.9/site-packageslist"
    assert "--all" in args0[0]
    assert "--" in args0[0]
    assert f":(exclude){exclude_paths[0]}" in args0[0]
    assert kwargs0["cwd"] == repo_path

    _assert_metadata_call(
        mock_subprocess_run.call_args_list[1],
        "commit1hash",
        repo_path,
        exclude_paths,
        is_exclude_test=True,
    )

    _assert_numstat_call(
        mock_subprocess_run.call_args_list[2],
        "commit1hash",
        repo_path,
        exclude_paths,
        is_exclude_test=True,
    )

    _assert_name_status_call(
        mock_subprocess_run.call_args_list[3],
        "commit1hash",
        repo_path,
        exclude_paths,
        is_exclude_test=True,
    )

    _assert_metadata_call(
        mock_subprocess_run.call_args_list[4],
        "commit2hash",
        repo_path,
        exclude_paths,
        is_exclude_test=True,
    )

    _assert_numstat_call(
        mock_subprocess_run.call_args_list[5],
        "commit2hash",
        repo_path,
        exclude_paths,
        is_exclude_test=True,
    )

    _assert_name_status_call(
        mock_subprocess_run.call_args_list[6],
        "commit2hash",
        repo_path,
        exclude_paths,
        is_exclude_test=True,
    )
