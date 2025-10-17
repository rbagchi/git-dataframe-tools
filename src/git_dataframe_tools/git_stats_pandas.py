import pandas as pd
import math
from typing import Optional


def parse_git_log(git_data: pd.DataFrame) -> list[dict]:
    """Parses git log data (provided as a DataFrame from git2df) and prepares author statistics."""
    author_stats_df = _get_author_stats_dataframe_internal(git_data)
    return author_stats_df.to_dict(orient="records")


def _calculate_deciles(
    df: pd.DataFrame, sort_by_col: str, decile_col_name: str
) -> pd.DataFrame:
    if df.empty:
        df[decile_col_name] = pd.Series(dtype=pd.Int64Dtype())
        return df

    # Sort the DataFrame by the specified column in descending order
    df_sorted = df.sort_values(by=sort_by_col, ascending=False).reset_index(drop=True)

    # Calculate deciles using qcut
    # qcut requires at least 2 unique values to create quantiles. If not enough, use cut.
    if df_sorted[sort_by_col].nunique() > 1:
        df_sorted[decile_col_name] = (
            pd.qcut(
                df_sorted[sort_by_col],
                q=10,
                labels=False,
                duplicates="drop",
            )
            .fillna(0)  # Fill NaN for dropped duplicates, if any
            .astype(int) + 1 # qcut labels are 0-9, convert to 1-10
        )
    else:
        # If all values are the same or only one unique value, assign all to decile 1
        df_sorted[decile_col_name] = 1

    # Ensure decile column is of Int64Dtype
    df_sorted[decile_col_name] = df_sorted[decile_col_name].astype(pd.Int64Dtype())

    return df_sorted


def _calculate_and_merge_deciles(author_stats: pd.DataFrame) -> pd.DataFrame:
    # Calculate diff_decile
    author_stats_diff_sorted = _calculate_deciles(author_stats, "total", "diff_decile")

    # Calculate commit_decile
    author_stats_commit_sorted = _calculate_deciles(
        author_stats, "commits", "commit_decile"
    )

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
    return author_stats

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

    author_stats = _calculate_and_merge_deciles(author_stats)

    # Sort by total diff size (descending) for consistent output order
    author_stats = author_stats.sort_values(by="total", ascending=False).reset_index(
        drop=True
    )

    return author_stats


def _author_matches_query(author: dict, query_parts: list[str]) -> bool:
    for part in query_parts:
        if (
            part in author["author_name"].lower()
            or part in author["author_email"].lower()
        ):
            return True
    return False

def find_author_stats(
    author_stats: list[dict], author_query: Optional[str]
) -> list[dict]:
    """
    Finds and returns stats for a specific author from the author statistics list.
    If author_query is None, returns all author_stats.
    """
    if not author_stats:
        return []

    if author_query is None:
        return author_stats

    query_parts = [p.strip().lower() for p in author_query.split("|")]
    return [author for author in author_stats if _author_matches_query(author, query_parts)]


def get_ranking(author_stats: list[dict]) -> list[dict]:
    """
    Returns the author statistics list sorted by total diff for printing.
    """
    if not author_stats:
        return []
    return sorted(author_stats, key=lambda x: x["total"], reverse=True)
