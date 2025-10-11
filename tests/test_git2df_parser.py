import pytest
import json
from datetime import datetime
from pathlib import Path
import dataclasses

from git2df.git_parser import (
    _parse_commit_metadata_line,
    _parse_file_stat_line,
    FileChange,
    parse_git_log,
)


def get_golden_file_pairs():
    data_dir = Path(__file__).parent / "data"
    for log_file in data_dir.glob("*.log"):
        json_file = log_file.with_suffix(".json")
        if json_file.exists():
            yield log_file, json_file


@pytest.mark.parametrize("log_file, json_file", get_golden_file_pairs())
def test_parse_git_data_internal(log_file, json_file):
    """Test _parse_git_data_internal with golden files."""
    with open(log_file, "r") as f:
        git_log_output = f.read()

    with open(json_file, "r") as f:
        expected_output_json = json.load(f)

    # Convert date strings in expected output to datetime objects
    for item in expected_output_json:
        if "commit_date" in item and isinstance(item["commit_date"], str):
            item["commit_date"] = datetime.fromisoformat(
                item["commit_date"]
            )  # iso-strict format
        if "file_changes" in item:
            for change in item["file_changes"]:
                # Ensure change_type is a string, not bytes if it was loaded as such
                if "change_type" in change and isinstance(change["change_type"], bytes):
                    change["change_type"] = change["change_type"].decode("utf-8")

    result = parse_git_log(git_log_output)
    # Convert dataclass objects to dictionaries for comparison
    result_as_dicts = [dataclasses.asdict(entry) for entry in result]
    assert result_as_dicts == expected_output_json


# New tests for _parse_commit_metadata_line


def test_parse_commit_metadata_line_valid():
    line = "@@@COMMIT@@@a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@p1p2p3p4p5p6p7p8p9d0e1f2a3b4c5d6e7f8a9b0@@@FIELD@@@John Doe@@@FIELD@@@john.doe@example.com@@@FIELD@@@2023-10-26T10:00:00+00:00\t1698307200@@@FIELD@@@---MSG_START---Initial commit message---MSG_END---"
    expected = {
        "commit_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "parent_hash": "p1p2p3p4p5p6p7p8p9d0e1f2a3b4c5d6e7f8a9b0",
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
        "parent_hash": None,
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


# New tests for _parse_file_stat_line
def test_parse_file_stat_line_valid_modified():
    line = "10\t5\tM\tfile.txt"
    expected = FileChange(
        file_path="file.txt", additions=10, deletions=5, change_type="M"
    )
    result = _parse_file_stat_line(line)
    assert result == expected


def test_parse_file_stat_line_valid_no_explicit_type():
    line = "10\t5\tfile.txt"
    expected = FileChange(
        file_path="file.txt", additions=10, deletions=5, change_type="M"
    )  # Defaults to M
    result = _parse_file_stat_line(line)
    assert result == expected


def test_parse_file_stat_line_valid_added():
    line = "10\t0\tA\tnew_file.txt"
    expected = FileChange(
        file_path="new_file.txt", additions=10, deletions=0, change_type="A"
    )
    result = _parse_file_stat_line(line)
    assert result == expected


def test_parse_file_stat_line_valid_deleted():
    line = "0\t5\tD\tdeleted_file.txt"
    expected = FileChange(
        file_path="deleted_file.txt", additions=0, deletions=5, change_type="D"
    )
    result = _parse_file_stat_line(line)
    assert result == expected


def test_parse_file_stat_line_valid_dash_stats():
    line = "-\t-\tfile_with_no_stats.txt"
    expected = FileChange(
        file_path="file_with_no_stats.txt", additions=0, deletions=0, change_type="M"
    )
    result = _parse_file_stat_line(line)
    assert result == expected


def test_parse_file_stat_line_malformed_missing_path():
    line = "10\t5\tM"
    result = _parse_file_stat_line(line)
    assert result is None


def test_parse_file_stat_line_malformed_bad_numbers():
    line = "abc\tdef\tM\tfile.txt"
    result = _parse_file_stat_line(line)
    assert result is None


def test_parse_file_stat_line_malformed_extra_fields():
    line = "10\t5\tM\tfile.txt\textra"
    expected = FileChange(
        file_path="file.txt\textra", additions=10, deletions=5, change_type="M"
    )
    result = _parse_file_stat_line(line)
    assert result == expected
