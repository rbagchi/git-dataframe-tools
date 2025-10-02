from collections import defaultdict
from git2df.git_parser import _parse_git_data_internal

def test_parse_git_data_internal_basic():
    """Test _parse_git_data_internal with basic git log output."""
    git_log_output = [
        "--commit1hash--Author One--author1@example.com--2023-01-01 10:00:00 +0000--Subject 1",
        "10\t5\tfile1.txt",
        "--commit2hash--Author Two--author2@example.com--2023-01-02 11:00:00 +0000--Subject 2",
        "20\t0\tfile2.py",
        "--commit3hash--Author One--author1@example.com--2023-01-03 12:00:00 +0000--Subject 3",
        "0\t15\tfile3.md",
        "-	-	binary_file.bin",
        "", # Empty line separator
        "--commit4hash--Author Three--author3@example.com--2023-01-04 13:00:00 +0000--Subject 4",
        "5\t5\tfile4.js"
    ]

    expected_authors = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set(),
        'commit_hashes': []
    })

    expected_authors['author1@example.com'] = {
        'name': 'Author One',
        'added': 10,
        'deleted': 20, # 5 from file1.txt + 15 from file3.md
        'total': 30,
        'commits': {'commit1hash', 'commit3hash'},
        'commit_hashes': ['commit1hash', 'commit3hash']
    }
    expected_authors['author2@example.com'] = {
        'name': 'Author Two',
        'added': 20,
        'deleted': 0,
        'total': 20,
        'commits': {'commit2hash'},
        'commit_hashes': ['commit2hash']
    }
    expected_authors['author3@example.com'] = {
        'name': 'Author Three',
        'added': 5,
        'deleted': 5,
        'total': 10,
        'commits': {'commit4hash'},
        'commit_hashes': ['commit4hash']
    }

    result = _parse_git_data_internal(git_log_output)

    # Convert sets to sorted lists for consistent comparison
    for email, data in result.items():
        data['commits'] = sorted(list(data['commits']))
    for email, data in expected_authors.items():
        data['commits'] = sorted(list(data['commits']))

    assert result == expected_authors

def test_parse_git_data_internal_empty_input():
    """Test _parse_git_data_internal with empty input."""
    git_log_output = []
    result = _parse_git_data_internal(git_log_output)
    assert result == defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set(),
        'commit_hashes': []
    })

def test_parse_git_data_internal_no_file_stats():
    """Test _parse_git_data_internal with commits but no file stats."""
    git_log_output = [
        "--commit1hash--Author One--author1@example.com--2023-01-01 10:00:00 +0000--Subject 1",
        "--commit2hash--Author Two--author2@example.com--2023-01-02 11:00:00 +0000--Subject 2",
    ]
    result = _parse_git_data_internal(git_log_output)
    expected_authors = defaultdict(lambda: {
        'name': '',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': set(),
        'commit_hashes': []
    })
    expected_authors['author1@example.com'] = {
        'name': 'Author One',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': {'commit1hash'},
        'commit_hashes': ['commit1hash']
    }
    expected_authors['author2@example.com'] = {
        'name': 'Author Two',
        'added': 0,
        'deleted': 0,
        'total': 0,
        'commits': {'commit2hash'},
        'commit_hashes': ['commit2hash']
    }

    # Convert sets to sorted lists for consistent comparison
    for email, data in result.items():
        data['commits'] = sorted(list(data['commits']))
    for email, data in expected_authors.items():
        data['commits'] = sorted(list(data['commits']))

    assert result == expected_authors
