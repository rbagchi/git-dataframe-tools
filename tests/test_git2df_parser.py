from datetime import datetime
from pathlib import Path

from git2df.git_parser._commit_metadata_parser import _parse_commit_metadata_line
from git2df.git_parser._file_stat_parser import (
    FileChange,
    _parse_numstat_line,
    _parse_name_status_line,
)

def get_golden_file_pairs():
    data_dir = Path(__file__).parent / "data"
    for log_file in data_dir.glob("*.log"):
        json_file = log_file.with_suffix(".json")
        if json_file.exists():
            yield log_file, json_file


# New tests for _parse_commit_metadata_line


def test_parse_commit_metadata_line_valid():
    line = "@@@COMMIT@@@a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@p1p2p3p4p5p6p7p8p9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@John Doe@@@FIELD@@@john.doe@example.com@@@FIELD@@@2023-10-26T10:00:00+00:00\t1698307200@@@FIELD@@@---MSG_START---Initial commit message---MSG_END---"
    expected = {
        "commit_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "parent_hashes": ["p1p2p3p4p5p6p7p8p9d0e1f2a3b4c5d6e7f8a9b0"],
        "author_name": "John Doe",
        "author_email": "john.doe@example.com",
        "commit_date": datetime.fromisoformat("2023-10-26T10:00:00+00:00"),
        "commit_timestamp": 1698307200,
        "commit_message": "Initial commit message",
    }
    result = _parse_commit_metadata_line(line)
    assert result == expected


def test_parse_commit_metadata_line_no_parent_hash():
    line = "@@@COMMIT@@@a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@@@@FIELD@@@John Doe@@@FIELD@@@john.doe@example.com@@@FIELD@@@2023-10-26T10:00:00+00:00\t1698307200@@@FIELD@@@---MSG_START---Initial commit message---MSG_END---"
    expected = {
        "commit_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "parent_hashes": [],
        "author_name": "John Doe",
        "author_email": "john.doe@example.com",
        "commit_date": datetime.fromisoformat("2023-10-26T10:00:00+00:00"),
        "commit_timestamp": 1698307200,
        "commit_message": "Initial commit message",
    }
    result = _parse_commit_metadata_line(line)
    assert result == expected


def test_parse_commit_metadata_line_malformed_missing_fields():
    line = "@@@COMMIT@@@a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@John Doe@@@FIELD@@@john.doe@example.com@@@FIELD@@@---MSG_START---Initial commit message---MSG_END---"  # Missing parent hash and date/timestamp
    result = _parse_commit_metadata_line(line)
    assert result is None


def test_parse_commit_metadata_line_malformed_bad_date_format():
    line = "@@@COMMIT@@@a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@@@@FIELD@@@John Doe@@@FIELD@@@john.doe@example.com@@@FIELD@@@BAD_DATE\t1698307200@@@FIELD@@@---MSG_START---Initial commit message---MSG_END---"
    result = _parse_commit_metadata_line(line)
    assert result is None


def test_parse_commit_metadata_line_malformed_no_commit_marker():
    line = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@@@@FIELD@@@John Doe@@@FIELD@@@john.doe@example.com@@@FIELD@@@2023-10-26T10:00:00+00:00\t1698307200@@@FIELD@@@---MSG_START---Initial commit message---MSG_END---"
    result = _parse_commit_metadata_line(line)
    assert result is None


# New tests for _parse_numstat_line
def test_parse_numstat_line_valid():
    line = "10\t5\tfile.txt"
    expected = FileChange(
        file_path="file.txt", additions=10, deletions=5, change_type=""
    )
    result = _parse_numstat_line(line)
    assert result == expected


def test_parse_numstat_line_dash_stats():
    line = "-\t-\tfile_with_no_stats.txt"
    expected = FileChange(
        file_path="file_with_no_stats.txt", additions=0, deletions=0, change_type=""
    )
    result = _parse_numstat_line(line)
    assert result == expected


def test_parse_numstat_line_malformed_too_few_parts():
    line = "10\t5"
    result = _parse_numstat_line(line)
    assert result is None


def test_parse_numstat_line_malformed_bad_numbers():
    line = "abc\tdef\tfile.txt"
    result = _parse_numstat_line(line)
    assert result is None


def test_parse_numstat_line_malformed_empty_path():
    line = "10\t5\t"
    result = _parse_numstat_line(line)
    assert result is None


# New tests for _parse_name_status_line
def test_parse_name_status_line_modified():
    line = "M\tfile.txt"
    expected = FileChange(
        file_path="file.txt", additions=0, deletions=0, change_type="M"
    )
    result = _parse_name_status_line(line)
    assert result == expected


def test_parse_name_status_line_added():
    line = "A\tnew_file.txt"
    expected = FileChange(
        file_path="new_file.txt", additions=0, deletions=0, change_type="A"
    )
    result = _parse_name_status_line(line)
    assert result == expected


def test_parse_name_status_line_deleted():
    line = "D\tdeleted_file.txt"
    expected = FileChange(
        file_path="deleted_file.txt", additions=0, deletions=0, change_type="D"
    )
    result = _parse_name_status_line(line)
    assert result == expected


def test_parse_name_status_line_renamed():
    line = "R100\told_name.txt\tnew_name.txt"
    expected = FileChange(
        file_path="new_name.txt", additions=0, deletions=0, change_type="R100", old_file_path="old_name.txt"
    )
    result = _parse_name_status_line(line)
    assert result == expected


def test_parse_name_status_line_copied():
    line = "C090\tsrc_file.txt\tdest_file.txt"
    expected = FileChange(
        file_path="dest_file.txt", additions=0, deletions=0, change_type="C090", old_file_path="src_file.txt"
    )
    result = _parse_name_status_line(line)
    assert result == expected


def test_parse_name_status_line_malformed_empty_line():
    line = ""
    result = _parse_name_status_line(line)
    assert result is None


def test_parse_name_status_line_malformed_no_path():
    line = "M"
    result = _parse_name_status_line(line)
    assert result is None


def test_parse_name_status_line_malformed_no_change_type():
    line = "\tfile.txt"
    result = _parse_name_status_line(line)
    assert result is None
