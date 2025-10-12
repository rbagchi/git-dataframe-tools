from unittest.mock import patch, MagicMock
from git2df.backends import GitCliBackend


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_no_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.side_effect = [
        # 1. git rev-list output
        MagicMock(stdout="commit1hash\n"),
        # 2. git show for metadata
        MagicMock(
            stdout=(
                "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
            )
        ),
        # 3. git show for numstat
        MagicMock(stdout="10\t5\tfile1.txt\n"),
        # 4. git show for name-status
        MagicMock(stdout="M\tfile1.txt\n"),
    ]

    repo_path = "/test/repo"
    backend = GitCliBackend(repo_path)

    # Act
    output = backend.get_raw_log_output()
    expected_output = (
        "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
        "10\t5\tM\tfile1.txt"
    )
    assert output == expected_output
    assert mock_subprocess_run.call_count == 4  # Called four times

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert "rev-list" in args0[0]
    assert "--all" in args0[0]
    assert kwargs0["cwd"] == repo_path

    # Assertions for the second call (metadata only)
    args1, kwargs1 = mock_subprocess_run.call_args_list[1]
    assert "show" in args1[0]
    assert "commit1hash" in args1[0]
    assert "--numstat" not in args1[0]
    assert "--name-status" not in args1[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args1[0]
    )
    assert kwargs1["cwd"] == repo_path

    # Assertions for the third call (numstat)
    args2, kwargs2 = mock_subprocess_run.call_args_list[2]
    assert "show" in args2[0]
    assert "commit1hash" in args2[0]
    assert "--numstat" in args2[0]
    assert "--name-status" not in args2[0]
    assert kwargs2["cwd"] == repo_path

    # Assertions for the fourth call (name-status)
    args3, kwargs3 = mock_subprocess_run.call_args_list[3]
    assert "show" in args3[0]
    assert "commit1hash" in args3[0]
    assert "--name-status" in args3[0]
    assert "--numstat" not in args3[0]
    assert kwargs3["cwd"] == repo_path


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_filters(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.side_effect = [
        # 1. git rev-list output
        MagicMock(stdout="commit1hash\n"),
        # 2. git show for metadata
        MagicMock(
            stdout=(
                "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
            )
        ),
        # 3. git show for numstat
        MagicMock(stdout="10\t5\tfile1.txt\n"),
        # 4. git show for name-status
        MagicMock(stdout="M\tfile1.txt\n"),
    ]

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
    assert mock_subprocess_run.call_count == 4

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert "rev-list" in args0[0]
    assert "--all" in args0[0]
    assert "--since" in args0[0]
    assert since in args0[0]
    assert "--until" in args0[0]
    assert until in args0[0]
    assert "--author" in args0[0]
    assert author in args0[0]
    assert "--grep" in args0[0]
    assert grep in args0[0]
    assert kwargs0["cwd"] == repo_path

    # Assertions for the second call (metadata only)
    args1, kwargs1 = mock_subprocess_run.call_args_list[1]
    assert "show" in args1[0]
    assert "commit1hash" in args1[0]
    assert "--numstat" not in args1[0]
    assert "--name-status" not in args1[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args1[0]
    )
    assert kwargs1["cwd"] == repo_path

    # Assertions for the third call (numstat)
    args2, kwargs2 = mock_subprocess_run.call_args_list[2]
    assert "show" in args2[0]
    assert "commit1hash" in args2[0]
    assert "--numstat" in args2[0]
    assert "--name-status" not in args2[0]
    assert kwargs2["cwd"] == repo_path

    # Assertions for the fourth call (name-status)
    args3, kwargs3 = mock_subprocess_run.call_args_list[3]
    assert "show" in args3[0]
    assert "commit1hash" in args3[0]
    assert "--name-status" in args3[0]
    assert "--numstat" not in args3[0]
    assert kwargs3["cwd"] == repo_path


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_merges(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.side_effect = [
        # 1. git rev-list output
        MagicMock(stdout="commit1hash\n"),
        # 2. git show for metadata
        MagicMock(
            stdout=(
                "@@@COMMIT@@@commit1hash@@@FIELD@@@parent1hash@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Merge commit---MSG_END---\n"
            )
        ),
        # 3. git show for numstat
        MagicMock(stdout="10\t5\tfile1.txt\n"),
        # 4. git show for name-status
        MagicMock(stdout="M\tfile1.txt\n"),
    ]

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
    assert mock_subprocess_run.call_count == 4

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert "rev-list" in args0[0]
    assert "--all" in args0[0]
    assert "--merges" in args0[0]
    assert f"origin/{mock_get_default_branch.return_value}" in args0[0]
    assert kwargs0["cwd"] == repo_path

    # Assertions for the second call (metadata only)
    args1, kwargs1 = mock_subprocess_run.call_args_list[1]
    assert "show" in args1[0]
    assert "commit1hash" in args1[0]
    assert "--numstat" not in args1[0]
    assert "--name-status" not in args1[0]
    assert (
        "--pretty=format:@@@COMMIT@@@%H@@@FIELD@@@%P@@@FIELD@@@%an@@@FIELD@@@%ae@@@FIELD@@@%ad%x09%at@@@FIELD@@@---MSG_START---%B---MSG_END---"
        in args1[0]
    )
    assert kwargs1["cwd"] == repo_path

    # Assertions for the third call (numstat)
    args2, kwargs2 = mock_subprocess_run.call_args_list[2]
    assert "show" in args2[0]
    assert "commit1hash" in args2[0]
    assert "--numstat" in args2[0]
    assert "--name-status" not in args2[0]
    assert kwargs2["cwd"] == repo_path

    # Assertions for the fourth call (name-status)
    args3, kwargs3 = mock_subprocess_run.call_args_list[3]
    assert "show" in args3[0]
    assert "commit1hash" in args3[0]
    assert "--name-status" in args3[0]
    assert "--numstat" not in args3[0]
    assert kwargs3["cwd"] == repo_path


@patch("git2df.backends.GitCliBackend._get_default_branch", return_value="main")
@patch("subprocess.run")
def test_get_raw_log_output_with_paths(mock_subprocess_run, mock_get_default_branch):
    # Arrange
    # Mock subprocess.run
    mock_subprocess_run.side_effect = [
        # 1. git rev-list output
        MagicMock(stdout="commit1hash\n"),
        # 2. git show for metadata
        MagicMock(
            stdout=(
                "@@@COMMIT@@@commit1hash@@@FIELD@@@@@@FIELD@@@Author One@@@FIELD@@@author1@example.com@@@FIELD@@@2023-01-01T10:00:00+00:00\t1672531200@@@FIELD@@@---MSG_START---Subject 1---MSG_END---\n"
            )
        ),
        # 3. git show for numstat
        MagicMock(stdout="10\t5\tsrc/file1.txt\n"),
        # 4. git show for name-status
        MagicMock(stdout="M\tsrc/file1.txt\n"),
    ]

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
    assert mock_subprocess_run.call_count == 4

    # Assertions for the first call (rev-list)
    args0, kwargs0 = mock_subprocess_run.call_args_list[0]
    assert "rev-list" in args0[0]
    assert "--all" in args0[0]
    assert "--" in args0[0]
    assert include_paths[0] in args0[0]
    assert kwargs0["cwd"] == repo_path

    # Assertions for the second call (metadata only)
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
    assert include_paths[0] in args1[0]
    assert kwargs1["cwd"] == repo_path

    # Assertions for the third call (numstat)
    args2, kwargs2 = mock_subprocess_run.call_args_list[2]
    assert "show" in args2[0]
    assert "commit1hash" in args2[0]
    assert "--numstat" in args2[0]
    assert "--name-status" not in args2[0]
    assert "--" in args2[0]
    assert include_paths[0] in args2[0]
    assert kwargs2["cwd"] == repo_path

    # Assertions for the fourth call (name-status)
    args3, kwargs3 = mock_subprocess_run.call_args_list[3]
    assert "show" in args3[0]
    assert "commit1hash" in args3[0]
    assert "--name-status" in args3[0]
    assert "--numstat" not in args3[0]
    assert "--" in args3[0]
    assert include_paths[0] in args3[0]
    assert kwargs3["cwd"] == repo_path


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
