import pandas as pd
import re
from typing import Optional

from git_dataframe_tools.git_stats_pandas import (
    parse_git_log,
    find_author_stats,
    get_ranking,
)


def _parse_mock_commit_info_line(line: str) -> dict:
    parts = line.split("--")
    if len(parts) >= 5:
        return {
            "commit_hash": parts[1],
            "author_name": parts[2],
            "author_email": parts[3],
            "commit_message": parts[4],
        }
    return {}


def _parse_mock_stat_line(line: str) -> Optional[dict]:
    stat_match = re.match(r"^(\d+|-)\t(\d+|-)\t(.+)$", line)
    if stat_match:
        added_str, deleted_str, filepath = stat_match.groups()
        added = 0 if added_str == "-" else int(added_str)
        deleted = 0 if deleted_str == "-" else int(deleted_str)
        return {"additions": added, "deletions": deleted, "file_paths": filepath}
    return None


def _mock_git_data_to_df(mock_git_data_str: list[str]) -> pd.DataFrame:
    """Helper to convert mock git log string to a DataFrame similar to git2df output."""
    data = []
    current_commit_info = {}

    for line in mock_git_data_str:
        line = line.strip()
        if not line:
            continue

        if line.startswith("--"):
            current_commit_info = _parse_mock_commit_info_line(line)
        else:
            stat_info = _parse_mock_stat_line(line)
            if stat_info and current_commit_info:
                data.append({**current_commit_info, **stat_info})

    if not data:
        return pd.DataFrame(
            columns=[
                "commit_hash",
                "parent_hash",
                "author_name",
                "author_email",
                "commit_message",
                "additions",
                "deletions",
                "file_paths",
            ],
        )

    df = pd.DataFrame(data)
    df["additions"] = df["additions"].astype(int)
    df["deletions"] = df["deletions"].astype(int)
    return df


def test_parse_git_log_empty_input():
    git_data_df = _mock_git_data_to_df([])
    author_stats = parse_git_log(git_data_df)
    assert author_stats == []


def _assert_single_author_stats(
    author_stats: list[dict],
    expected_email: str,
    expected_name: str,
    expected_added: int,
    expected_deleted: int,
    expected_total: int,
    expected_commits: int,
):
    assert len(author_stats) == 1
    assert author_stats[0]["author_email"] == expected_email
    assert author_stats[0]["author_name"] == expected_name
    assert author_stats[0]["added"] == expected_added
    assert author_stats[0]["deleted"] == expected_deleted
    assert author_stats[0]["total"] == expected_total
    assert author_stats[0]["commits"] == expected_commits


def test_parse_git_log_single_commit_single_file():
    git_data_str = [
        "--commit_hash1--Author Name--author@example.com--Commit message 1",
        "10\t5\tfile1.txt",
    ]
    git_data_df = _mock_git_data_to_df(git_data_str)
    author_stats = parse_git_log(git_data_df)
    _assert_single_author_stats(
        author_stats, "author@example.com", "Author Name", 10, 5, 15, 1
    )


def _assert_author_stats_entry(
    author_entry: dict,
    expected_name: str,
    expected_added: int,
    expected_deleted: int,
    expected_total: int,
    expected_commits: int,
):
    assert author_entry["author_name"] == expected_name
    assert author_entry["added"] == expected_added
    assert author_entry["deleted"] == expected_deleted
    assert author_entry["total"] == expected_total
    assert author_entry["commits"] == expected_commits


def test_parse_git_log_multiple_commits_multiple_files():
    git_data_str = [
        "--commit_hash1--Author One--one@example.com--Commit message A",
        "10\t5\tfileA.txt",
        "2\t1\tfileB.txt",
        "",
        "--commit_hash2--Author Two--two@example.com--Commit message B",
        "1\t1\tfileC.txt",
    ]
    git_data_df = _mock_git_data_to_df(git_data_str)
    author_stats = parse_git_log(git_data_df)
    assert len(author_stats) == 2

    author_one = next(a for a in author_stats if a["author_email"] == "one@example.com")
    _assert_author_stats_entry(author_one, "Author One", 12, 6, 18, 1)

    author_two = next(a for a in author_stats if a["author_email"] == "two@example.com")
    _assert_author_stats_entry(author_two, "Author Two", 1, 1, 2, 1)


def test_parse_git_log_binary_files():
    git_data_str = [
        "--commit_hash1--Author Name--author@example.com--Commit message 1",
        "-\t-\timage.png",
        "10\t5\tfile1.txt",
    ]
    git_data_df = _mock_git_data_to_df(git_data_str)
    author_stats = parse_git_log(git_data_df)
    assert len(author_stats) == 1
    assert author_stats[0]["added"] == 10
    assert author_stats[0]["deleted"] == 5


def test_get_author_stats_empty_input():
    git_data_df = _mock_git_data_to_df([])
    author_stats = parse_git_log(git_data_df)
    assert author_stats == []


def test_get_author_stats_basic():
    git_data_str = [
        "--commit1--Author A--a@example.com--msg1",
        "10\t5\tfile1.txt",
        "",
        "--commit2--Author B--b@example.com--msg2",
        "20\t10\tfile2.txt",
        "",
        "--commit3--Author A--a@example.com--msg3",
        "5\t2\tfile3.txt",
    ]
    git_data_df = _mock_git_data_to_df(git_data_str)
    author_stats = parse_git_log(git_data_df)

    assert len(author_stats) == 2

    author_a = next(a for a in author_stats if a["author_email"] == "a@example.com")
    _assert_author_stats_entry(author_a, "Author A", 15, 7, 22, 2)

    author_b = next(a for a in author_stats if a["author_email"] == "b@example.com")
    _assert_author_stats_entry(author_b, "Author B", 20, 10, 30, 1)


def _assert_author_decile_stats(
    author_entry: dict,
    expected_email: str,
    expected_rank: int,
    expected_diff_decile: int,
    expected_commit_decile: int,
):
    assert author_entry["author_email"] == expected_email
    assert author_entry["rank"] == expected_rank
    assert author_entry["diff_decile"] == expected_diff_decile
    assert author_entry["commit_decile"] == expected_commit_decile


def test_get_author_stats_ranks_deciles():
    git_data_str = [
        "--commit1--A--a@example.com--msg",
        "100\t0\tf1.txt",
        "",
        "--commit2--B--b@example.com--msg",
        "50\t0\tf2.txt",
        "",
        "--commit3--C--c@example.com--msg",
        "200\t0\tf3.txt",
        "",
        "--commit4--D--d@example.com--msg",
        "10\t0\tf4.txt",
    ]
    git_data_df = _mock_git_data_to_df(git_data_str)
    author_stats = parse_git_log(git_data_df)

    # Sort by total for easier assertion
    author_stats.sort(key=lambda x: x["total"], reverse=True)

    _assert_author_decile_stats(author_stats[0], "c@example.com", 1, 1, 1)
    _assert_author_decile_stats(author_stats[1], "a@example.com", 2, 5, 1)
    _assert_author_decile_stats(author_stats[2], "b@example.com", 3, 8, 1)
    _assert_author_decile_stats(author_stats[3], "d@example.com", 4, 10, 1)


def test_find_author_stats_found():
    author_stats = [
        {
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "added": 100,
            "deleted": 10,
            "total": 110,
            "commits": 5,
            "rank": 2,
            "diff_decile": 2,
            "commit_decile": 2,
        },
        {
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "added": 200,
            "deleted": 20,
            "total": 220,
            "commits": 10,
            "rank": 1,
            "diff_decile": 1,
            "commit_decile": 1,
        },
    ]

    matches = find_author_stats(author_stats, "john")
    assert len(matches) == 1
    assert matches[0]["author_name"] == "John Doe"


def test_find_author_stats_not_found():
    author_stats = [
        {
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "added": 100,
            "deleted": 10,
            "total": 110,
            "commits": 5,
            "rank": 2,
            "diff_decile": 2,
            "commit_decile": 2,
        },
        {
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "added": 200,
            "deleted": 20,
            "total": 220,
            "commits": 10,
            "rank": 1,
            "diff_decile": 1,
            "commit_decile": 1,
        },
    ]

    matches = find_author_stats(author_stats, "peter")
    assert matches == []


def test_get_ranking_basic():
    author_stats = [
        {
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "added": 100,
            "deleted": 10,
            "total": 110,
            "commits": 5,
            "rank": 2,
            "diff_decile": 2,
            "commit_decile": 2,
        },
        {
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "added": 200,
            "deleted": 20,
            "total": 220,
            "commits": 10,
            "rank": 1,
            "diff_decile": 1,
            "commit_decile": 1,
        },
    ]

    ranked_list = get_ranking(author_stats)
    assert len(ranked_list) == 2
    assert ranked_list[0]["author_name"] == "Jane Smith"  # Sorted by total descending
    assert ranked_list[1]["author_name"] == "John Doe"


def test_get_ranking_empty_input():
    author_stats = []
    ranked_list = get_ranking(author_stats)
    assert ranked_list == []
