import pytest
import subprocess
import os

from git2df.pygit2_backend import Pygit2Backend


def test_get_log_entries_metadata(git_repo):
    backend = Pygit2Backend(repo_path=git_repo)
    log_entries = backend.get_log_entries()

    assert len(log_entries) > 0

    entry = log_entries[-1]  # The first commit
    assert entry.author_name == "Default User"
    assert entry.author_email == "default@example.com"
    assert entry.commit_message == "Initial commit"


def test_get_log_entries_date_filtering(tmp_path):
    repo_path = tmp_path / "test_repo_date_filter"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    # Create one commit with a specific date
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Commit 1",
            "--date",
            "2023-01-01T10:00:00Z",
        ],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Commit 2",
            "--date",
            "2023-01-03T10:00:00Z",
        ],
        cwd=repo_path,
        check=True,
    )

    backend = Pygit2Backend(repo_path=repo_path)

    # Test since
    log_entries = backend.get_log_entries(since="2023-01-02")
    assert len(log_entries) == 1
    assert log_entries[0].commit_message == "Commit 2"

    # Test until
    log_entries = backend.get_log_entries(until="2023-01-02")
    assert len(log_entries) == 1
    assert log_entries[0].commit_message == "Commit 1"

    # Test since and until
    log_entries = backend.get_log_entries(since="2023-01-01", until="2023-01-01")
    assert len(log_entries) == 1
    assert log_entries[0].commit_message == "Commit 1"

    log_entries = backend.get_log_entries(since="2023-01-02", until="2023-01-02")
    assert len(log_entries) == 0


def test_get_log_entries_author_filtering(git_repo):
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Commit by Alice",
            '--author="Alice <alice@example.com>"',
            "--date",
            "2023-01-01T10:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Commit by Bob",
            '--author="Bob <bob@example.com>"',
            "--date",
            "2023-01-02T10:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )

    backend = Pygit2Backend(repo_path=git_repo)

    log_entries = backend.get_log_entries(author="Alice")
    assert len(log_entries) == 1
    assert log_entries[0].author_name == "Alice"

    log_entries = backend.get_log_entries(author="bob@example.com")
    assert len(log_entries) == 1
    assert log_entries[0].author_email == "bob@example.com"


def test_get_log_entries_grep_filtering(git_repo):
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Fix: bug in login",
            "--date",
            "2023-01-01T10:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Feat: add new feature",
            "--date",
            "2023-01-02T10:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )

    backend = Pygit2Backend(repo_path=git_repo)

    log_entries = backend.get_log_entries(grep="Fix")
    assert len(log_entries) == 1
    assert "Fix" in log_entries[0].commit_message

    log_entries = backend.get_log_entries(grep="Feat")
    assert len(log_entries) == 1
    assert "Feat" in log_entries[0].commit_message


def test_get_log_entries_path_filtering(git_repo):
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Add file1",
            "--date",
            "2023-01-01T10:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Add file2",
            "--date",
            "2023-01-02T10:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "Add file3",
            "--date",
            "2023-01-03T10:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )

    # Create files
    os.makedirs(f"{git_repo}/src", exist_ok=True)
    with open(f"{git_repo}/src/file1.txt", "w") as f:
        f.write("content1")
    subprocess.run(["git", "add", "src/file1.txt"], cwd=git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add src/file1.txt", "--date", "2023-01-04T10:00:00Z"],
        cwd=git_repo,
        check=True,
    )

    os.makedirs(f"{git_repo}/docs", exist_ok=True)
    with open(f"{git_repo}/docs/file2.txt", "w") as f:
        f.write("content2")
    subprocess.run(["git", "add", "docs/file2.txt"], cwd=git_repo, check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Add docs/file2.txt",
            "--date",
            "2023-01-05T10:00:00:00Z",
        ],
        cwd=git_repo,
        check=True,
    )

    backend = Pygit2Backend(repo_path=git_repo)

    # Test include_paths
    log_entries = backend.get_log_entries(include_paths=["src/"])
    assert len(log_entries) == 1
    assert log_entries[0].commit_message == "Add src/file1.txt"

    # Test exclude_paths
    log_entries = backend.get_log_entries(exclude_paths=["src/"])
    print('Log entries for exclude_paths="src/":')
    for entry in log_entries:
        print(f"  - {entry.commit_message} ({entry.file_changes})")
    assert len(log_entries) == 2
    assert log_entries[0].commit_message == "Add docs/file2.txt"

    # Test include_paths and exclude_paths
    log_entries = backend.get_log_entries(
        include_paths=["src/"], exclude_paths=["src/file1.txt"]
    )
    assert len(log_entries) == 0


def _setup_file_stats_repo(tmp_path):
    repo_path = tmp_path / "test_repo_file_stats"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    # Create a file and commit it
    file_path = repo_path / "test_file.txt"
    with open(file_path, "w") as f:
        f.write("line1\nline2\n")
    subprocess.run(["git", "add", "test_file.txt"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add test_file.txt", "--date", "2023-01-01T10:00:00Z"],
        cwd=repo_path,
        check=True,
    )

    # Modify the file
    with open(file_path, "w") as f:
        f.write("line1\nline2_modified\nline3_added\n")
    subprocess.run(["git", "add", "test_file.txt"], cwd=repo_path, check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Modify test_file.txt",
            "--date",
            "2023-01-02T10:00:00Z",
        ],
        cwd=repo_path,
        check=True,
    )

    # Delete the file
    os.remove(file_path)
    subprocess.run(["git", "rm", "test_file.txt"], cwd=repo_path, check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Delete test_file.txt",
            "--date",
            "2023-01-03T10:00:00Z",
        ],
        cwd=repo_path,
        check=True,
    )
    return Pygit2Backend(repo_path=repo_path)

@pytest.mark.parametrize(
    "grep_message, expected_additions, expected_deletions, expected_change_type",
    [
        ("Add test_file.txt", 2, 0, "A"),
        ("Modify test_file.txt", 2, 1, "M"),
        ("Delete test_file.txt", 0, 3, "D"),
    ],
)
def test_get_log_entries_file_stats_extraction(tmp_path, grep_message, expected_additions, expected_deletions, expected_change_type):
    backend = _setup_file_stats_repo(tmp_path)
    log_entries = backend.get_log_entries(grep=grep_message)
    assert len(log_entries) == 1
    file_change = log_entries[0].file_changes[0]
    assert file_change.file_path == "test_file.txt"
    assert file_change.additions == expected_additions
    assert file_change.deletions == expected_deletions
    assert file_change.change_type == expected_change_type


def _setup_rename_copy_repo(tmp_path):
    repo_path = tmp_path / "test_repo_rename_copy"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    backend = Pygit2Backend(repo_path=repo_path)

    # Test Rename
    file_a_path = repo_path / "file_a.txt"

    with open(file_a_path, "w") as f:
        f.write("content")
    subprocess.run(["git", "add", "file_a.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add file_a.txt"], cwd=repo_path, check=True)

    subprocess.run(["git", "mv", "file_a.txt", "file_b.txt"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Rename file_a.txt to file_b.txt"],
        cwd=repo_path,
        check=True,
    )

    # Test Copy
    file_c_path = repo_path / "file_c.txt"
    file_d_path = repo_path / "file_d.txt"
    with open(file_c_path, "w") as f:
        f.write("content")
    subprocess.run(["git", "add", "file_c.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add file_c.txt"], cwd=repo_path, check=True)

    subprocess.run(
        ["cp", str(file_c_path), str(file_d_path)], cwd=repo_path, check=True
    )
    subprocess.run(["git", "add", "file_d.txt"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Copy file_c.txt to file_d.txt"],
        cwd=repo_path,
        check=True,
    )
    return backend

@pytest.mark.parametrize(
    "grep_message, expected_file_path, expected_change_type, expected_additions, expected_deletions",
    [
        ("Rename file_a.txt to file_b.txt", "file_b.txt", "R", 0, 0),
        ("Copy file_c.txt to file_d.txt", "file_d.txt", "A", 1, 0),
    ],
)
def test_get_log_entries_file_path_for_renames_and_copies(tmp_path, grep_message, expected_file_path, expected_change_type, expected_additions, expected_deletions):
    backend = _setup_rename_copy_repo(tmp_path)
    log_entries = backend.get_log_entries(grep=grep_message)
    assert len(log_entries) == 1
    file_change = log_entries[0].file_changes[0]
    assert file_change.file_path == expected_file_path
    assert file_change.change_type == expected_change_type
    assert file_change.additions == expected_additions
    assert file_change.deletions == expected_deletions


def test_get_log_entries_initial_commit_file_stats(tmp_path):
    repo_path = tmp_path / "test_repo_initial_commit"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    backend = Pygit2Backend(repo_path=repo_path)

    # Create a file and make the initial commit
    file_path = repo_path / "initial_file.txt"
    with open(file_path, "w") as f:
        f.write("line1\nline2\nline3\n")
    subprocess.run(["git", "add", "initial_file.txt"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit with file"], cwd=repo_path, check=True
    )

    log_entries = backend.get_log_entries(grep="Initial commit with file")
    assert len(log_entries) == 1
    file_change = log_entries[0].file_changes[0]
    assert file_change.file_path == "initial_file.txt"
    assert file_change.additions == 3
    assert file_change.deletions == 0
    assert file_change.change_type == "A"


def _setup_advanced_path_filtering_repo(tmp_path):
    repo_path = tmp_path / "test_repo_path_filter_advanced"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )

    # Setup: Create files and commits
    (repo_path / "root_file.txt").write_text("root content")
    (repo_path / "src" / "module1").mkdir(parents=True)
    (repo_path / "src" / "module1" / "file1.txt").write_text("module1 content")
    (repo_path / "src" / "module2").mkdir(parents=True)
    (repo_path / "src" / "module2" / "file2.txt").write_text("module2 content")
    (repo_path / "docs").mkdir(parents=True)
    (repo_path / "docs" / "doc1.md").write_text("doc content")

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial files"], cwd=repo_path, check=True)

    return Pygit2Backend(repo_path=repo_path)

@pytest.mark.parametrize(
    "include_paths, exclude_paths, expected_file_paths",
    [
        # Test Case 1: Multiple include_paths
        (["src/module1/", "docs/"], None, ["src/module1/file1.txt", "docs/doc1.md"]),
        # Test Case 2: Multiple exclude_paths
        (None, ["src/", "root_file.txt"], ["docs/doc1.md"]),
        # Test Case 3: Exact file path include_paths
        (["src/module1/file1.txt"], None, ["src/module1/file1.txt"]),
        # Test Case 4: Exact file path exclude_paths
        (None, ["src/module2/file2.txt"], ["src/module1/file1.txt", "docs/doc1.md", "root_file.txt"]),
    ],
)
def test_get_log_entries_path_filtering_advanced(tmp_path, include_paths, exclude_paths, expected_file_paths):
    backend = _setup_advanced_path_filtering_repo(tmp_path)
    log_entries = backend.get_log_entries(include_paths=include_paths, exclude_paths=exclude_paths)
    assert len(log_entries) == 1  # Only the initial commit
    file_paths = [fc.file_path for fc in log_entries[0].file_changes]
    assert sorted(file_paths) == sorted(expected_file_paths)
