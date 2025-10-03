import pandas as pd
import re

from git_dataframe_tools.git_stats_pandas import (
    parse_git_log,
    find_author_stats,
    get_ranking,
)


def _mock_git_data_to_df(mock_git_data_str: list[str]) -> pd.DataFrame:
    """Helper to convert mock git log string to a DataFrame similar to git2df output."""
    lines = mock_git_data_str
    data = []
    current_commit_info = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("--"):
            parts = line.split("--")
            if len(parts) >= 5:
                current_commit_info = {
                    "commit_hash": parts[1],
                    "author_name": parts[2],
                    "author_email": parts[3],
                    "commit_message": parts[4],
                }
        else:
            stat_match = re.match(r"^(\d+|-)\t(\d+|-)\t(.+)$", line)
            if stat_match and current_commit_info:
                added_str, deleted_str, filepath = stat_match.groups()

                added = 0 if added_str == "-" else int(added_str)
                deleted = 0 if deleted_str == "-" else int(deleted_str)

                row = current_commit_info.copy()
                row.update(
                    {"additions": str(added), "deletions": str(deleted), "file_paths": filepath}
                )
                data.append(row)

    if not data:
        return pd.DataFrame(
            columns=[
                "commit_hash",
                "author_name",
                "author_email",
                "commit_message",
                "additions",
                "deletions",
                "file_paths",
            ]
        )

    df = pd.DataFrame(data)
    return df


def test_parse_git_log_empty_input():
    git_data_df = _mock_git_data_to_df([])
    author_stats = parse_git_log(git_data_df)
    assert author_stats == []


def test_parse_git_log_single_commit_single_file():
    git_data_str = [
        "--commit_hash1--Author Name--author@example.com--Commit message 1",
        "10\t5\tfile1.txt",
    ]
    git_data_df = _mock_git_data_to_df(git_data_str)
    author_stats = parse_git_log(git_data_df)
    assert len(author_stats) == 1
    assert author_stats[0]["author_email"] == "author@example.com"
    assert author_stats[0]["author_name"] == "Author Name"
    assert author_stats[0]["added"] == 10
    assert author_stats[0]["deleted"] == 5
    assert author_stats[0]["total"] == 15
    assert author_stats[0]["commits"] == 1


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
    assert author_one["author_name"] == "Author One"
    assert author_one["added"] == 12
    assert author_one["deleted"] == 6
    assert author_one["total"] == 18
    assert author_one["commits"] == 1

    author_two = next(a for a in author_stats if a["author_email"] == "two@example.com")
    assert author_two["author_name"] == "Author Two"
    assert author_two["added"] == 1
    assert author_two["deleted"] == 1
    assert author_two["total"] == 2
    assert author_two["commits"] == 1


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
    assert author_a["author_name"] == "Author A"
    assert author_a["added"] == 15
    assert author_a["deleted"] == 7
    assert author_a["total"] == 22
    assert author_a["commits"] == 2

    author_b = next(a for a in author_stats if a["author_email"] == "b@example.com")
    assert author_b["author_name"] == "Author B"
    assert author_b["added"] == 20
    assert author_b["deleted"] == 10
    assert author_b["total"] == 30
    assert author_b["commits"] == 1


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

    # C: total 200, commits 1
    assert author_stats[0]["author_email"] == "c@example.com"
    assert author_stats[0]["rank"] == 1
    assert author_stats[0]["diff_decile"] == 1
    assert (
        author_stats[0]["commit_decile"] == 1
    )  # All have 1 commit, so all are in decile 1

    # A: total 100, commits 1
    assert author_stats[1]["author_email"] == "a@example.com"
    assert author_stats[1]["rank"] == 2
    assert author_stats[1]["diff_decile"] == 5
    assert author_stats[1]["commit_decile"] == 1
    # B: total 50, commits 1
    assert author_stats[2]["author_email"] == "b@example.com"
    assert author_stats[2]["rank"] == 3
    assert author_stats[2]["diff_decile"] == 8
    assert author_stats[2]["commit_decile"] == 1

    # D: total 10, commits 1
    assert author_stats[3]["author_email"] == "d@example.com"
    assert author_stats[3]["rank"] == 4
    assert author_stats[3]["diff_decile"] == 10
    assert author_stats[3]["commit_decile"] == 1


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
