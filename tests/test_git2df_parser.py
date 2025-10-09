import pytest
import json
from pathlib import Path
from datetime import datetime
from git2df.git_parser import _parse_git_data_internal


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
        git_log_output = f.read().splitlines()

    with open(json_file, "r") as f:
        expected_output_json = json.load(f)

    # Convert date strings in expected output to datetime objects
    for item in expected_output_json:
        if "commit_date" in item and isinstance(item["commit_date"], str):
            item["commit_date"] = datetime.fromisoformat(item["commit_date"])

    result = _parse_git_data_internal(git_log_output)
    assert result == expected_output_json
