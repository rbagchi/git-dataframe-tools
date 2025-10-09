import pandas as pd
import math


def _calculate_decile_from_rank(rank, n):
    return min(10, math.ceil(rank * 10 / n))


def parse_git_log(git_data: pd.DataFrame) -> list[dict]:
    """Parses git log data (provided as a DataFrame from git2df) and prepares author statistics."""
    author_stats_df = _get_author_stats_dataframe_internal(git_data)
    return author_stats_df.to_dict(orient="records")


def _get_author_stats_dataframe_internal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates author statistics (added, deleted, total, commits, ranks, deciles)
    from a DataFrame of git log data.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "author_name",
                "author_email",
                "added",
                "deleted",
                "total",
                "commits",
                "rank",
                "diff_decile",
                "commit_decile",
            ]
        )

    # Aggregate by author
    author_stats = (
        df.groupby(["author_email", "author_name"])
        .agg(
            added=("additions", "sum"),
            deleted=("deletions", "sum"),
            commits=("commit_hash", "nunique"),
        )
        .reset_index()
    )

    if author_stats.empty:
        return pd.DataFrame(
            columns=[
                "author_name",
                "author_email",
                "added",
                "deleted",
                "total",
                "commits",
                "rank",
                "diff_decile",
                "commit_decile",
            ]
        )

    author_stats["total"] = author_stats["added"] + author_stats["deleted"]

    # Calculate ranks for total diff
    author_stats["rank"] = (
        author_stats["total"].rank(method="min", ascending=False).astype(int)
    )

    # Calculate diff_decile
    author_stats_diff_sorted = author_stats.sort_values(
        by="total", ascending=False
    ).reset_index(drop=True)
    n_diff = len(author_stats_diff_sorted)
    if n_diff > 0:
        current_decile_diff = 1
        for i in range(n_diff):
            current_total = author_stats_diff_sorted["total"].iloc[i]
            previous_total = author_stats_diff_sorted["total"].iloc[i - 1]
            if i > 0 and current_total < previous_total:
                current_rank_diff = i + 1
                current_decile_diff = min(
                    10, math.ceil(current_rank_diff * 10 / n_diff)
                )
            author_stats_diff_sorted.loc[i, "diff_decile"] = int(current_decile_diff)
    else:
        author_stats_diff_sorted["diff_decile"] = pd.Series(dtype=pd.Int64Dtype())

    # Calculate commit_decile
    author_stats_commit_sorted = author_stats.sort_values(
        by="commits", ascending=False
    ).reset_index(drop=True)
    n_commit = len(author_stats_commit_sorted)
    if n_commit > 0:
        current_decile_commit = 1
        for i in range(n_commit):
            current_commits = author_stats_commit_sorted["commits"].iloc[i]
            previous_commits = author_stats_commit_sorted["commits"].iloc[i - 1]
            if i > 0 and current_commits < previous_commits:
                current_rank_commit = i + 1
                current_decile_commit = min(
                    10, math.ceil(current_rank_commit * 10 / n_commit)
                )
            author_stats_commit_sorted.loc[i, "commit_decile"] = int(
                current_decile_commit
            )
    else:
        author_stats_commit_sorted["commit_decile"] = pd.Series(dtype=pd.Int64Dtype())

    # Merge diff_decile back to the original author_stats DataFrame
    author_stats = author_stats.merge(
        author_stats_diff_sorted[["author_email", "diff_decile"]],
        on="author_email",
        how="left",
    )

    # Merge commit_decile back to the original author_stats DataFrame
    author_stats = author_stats.merge(
        author_stats_commit_sorted[["author_email", "commit_decile"]],
        on="author_email",
        how="left",
    )

    # Ensure decile columns are of Int64Dtype after merge
    author_stats["diff_decile"] = author_stats["diff_decile"].astype(pd.Int64Dtype())
    author_stats["commit_decile"] = author_stats["commit_decile"].astype(
        pd.Int64Dtype()
    )

    # Sort by total diff size (descending) for consistent output order
    author_stats = author_stats.sort_values(by="total", ascending=False).reset_index(
        drop=True
    )

    if author_stats.empty:
        return pd.DataFrame(
            columns=[
                "author_name",
                "author_email",
                "added",
                "deleted",
                "total",
                "commits",
                "rank",
                "diff_decile",
                "commit_decile",
            ]
        )

    return author_stats


def find_author_stats(author_stats: list[dict], author_query: str | None) -> list[dict]:
    """
    Finds and returns stats for a specific author from the author statistics list.
    If author_query is None, returns all author_stats.
    """
    if not author_stats:
        return []

    if author_query is None:
        return author_stats

    query_parts = [p.strip().lower() for p in author_query.split("|")]
    matches = []
    for author in author_stats:
        for part in query_parts:
            if (
                part in author["author_name"].lower()
                or part in author["author_email"].lower()
            ):
                matches.append(author)
                break  # Match found for this author, move to next author
    return matches


def get_ranking(author_stats: list[dict]) -> list[dict]:
    """
    Returns the author statistics list sorted by total diff for printing.
    """
    if not author_stats:
        return []
    return sorted(author_stats, key=lambda x: x["total"], reverse=True)
