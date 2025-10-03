from datetime import datetime, timezone
from git2df.git_parser import _parse_git_data_internal

def test_parse_git_data_internal_commit_centric():
    """Test _parse_git_data_internal with commit-centric git log output."""
    git_log_output = [
        "--commit1hash--parent1hash--Author One--author1@example.com--2023-01-01T10:00:00+00:00--Subject 1",
        "10\t5\tfile1.txt",
        "2\t1\tfile2.py",
        "", # Empty line separator
        "--commit2hash----Author Two--author2@example.com--2023-01-02T11:00:00+00:00--Subject 2", # No parent hash
        "20\t0\tfile3.md",
        "-\t-\tbinary_file.bin", # Binary file, no changes
        "",
        "--commit3hash--parent3hash--Author One--author1@example.com--2023-01-03T12:00:00+00:00--Subject 3",
        "0\t15\tfile4.js", # Deletion
        "5\t0\tfile5.txt", # Addition
    ]

    expected_output = [
        {
            'commit_hash': 'commit1hash',
            'parent_hash': 'parent1hash',
            'author_name': 'Author One',
            'author_email': 'author1@example.com',
            'commit_date': datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 1',
            'file_paths': 'file1.txt',
            'change_type': 'M',
            'additions': 10,
            'deletions': 5
        },
        {
            'commit_hash': 'commit1hash',
            'parent_hash': 'parent1hash',
            'author_name': 'Author One',
            'author_email': 'author1@example.com',
            'commit_date': datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 1',
            'file_paths': 'file2.py',
            'change_type': 'M',
            'additions': 2,
            'deletions': 1
        },
        {
            'commit_hash': 'commit2hash',
            'parent_hash': None,
            'author_name': 'Author Two',
            'author_email': 'author2@example.com',
            'commit_date': datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 2',
            'file_paths': 'file3.md',
            'change_type': 'A',
            'additions': 20,
            'deletions': 0
        },
        {
            'commit_hash': 'commit2hash',
            'parent_hash': None,
            'author_name': 'Author Two',
            'author_email': 'author2@example.com',
            'commit_date': datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 2',
            'file_paths': 'binary_file.bin',
            'change_type': 'M',
            'additions': 0,
            'deletions': 0
        },
        {
            'commit_hash': 'commit3hash',
            'parent_hash': 'parent3hash',
            'author_name': 'Author One',
            'author_email': 'author1@example.com',
            'commit_date': datetime(2023, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 3',
            'file_paths': 'file4.js',
            'change_type': 'D',
            'additions': 0,
            'deletions': 15
        },
        {
            'commit_hash': 'commit3hash',
            'parent_hash': 'parent3hash',
            'author_name': 'Author One',
            'author_email': 'author1@example.com',
            'commit_date': datetime(2023, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            'commit_message': 'Subject 3',
            'file_paths': 'file5.txt',
            'change_type': 'A',
            'additions': 5,
            'deletions': 0
        },
    ]

    result = _parse_git_data_internal(git_log_output)
    assert result == expected_output

def test_parse_git_data_internal_empty_input():
    """Test _parse_git_data_internal with empty input."""
    git_log_output = []
    result = _parse_git_data_internal(git_log_output)
    assert result == []

def test_parse_git_data_internal_no_file_stats():
    """Test _parse_git_data_internal with commits but no file stats."""
    git_log_output = [
        "--commit1hash--parent1hash--Author One--author1@example.com--2023-01-01T10:00:00+00:00--Subject 1",
        "",
        "--commit2hash----Author Two--author2@example.com--2023-01-02T11:00:00+00:00--Subject 2",
    ]
    result = _parse_git_data_internal(git_log_output)
    assert result == []
