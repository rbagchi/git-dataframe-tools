from typing import Any, Dict, List
from tabulate import tabulate
import pandas as pd
from loguru import logger

from git_dataframe_tools.config_models import GitAnalysisConfig, OutputFormat


def format_as_markdown_table(df: pd.DataFrame) -> str:
    """Formats a Pandas DataFrame into a Markdown table string."""
    return df.to_markdown(index=False)


def _format_table_with_tabulate(headers: List[str], data: List[List[Any]]) -> str:
    """Formats data into a table string using the tabulate library."""
    return tabulate(data, headers=headers, tablefmt="grid")


def _get_matching_authors(
    config: GitAnalysisConfig, author_stats: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    author_query_lower = config.author_query.lower() if config.author_query else ""
    return [
        a
        for a in author_stats
        if author_query_lower in a["author_name"].lower()
        or author_query_lower in a["author_email"].lower()
    ]


def _log_no_author_matches(config: GitAnalysisConfig) -> None:
    analysis_type = "merged commits" if config.merged_only else "commits"
    logger.warning(f"No {analysis_type} found in the specified time period.")
    logger.error(f"No authors found matching '{config.author_query}'")
    print(
        "Suggestion: Try a partial match like first name, last name, or email domain."
    )


def _print_author_stats_detail(author: Dict[str, Any], total_authors: int) -> None:
    logger.info(f"Author: {author['author_name']} <{author['author_email']}>")
    print(f"  Rank:          #{author['rank']} of {total_authors} authors")
    print(f"  Lines Added:   {author['added']:,}")
    print(f"  Lines Deleted: {author['deleted']:,}")
    print(f"  Total Diff:    {author['total']:,}")
    print(f"  Commits:       {author['commits']}")
    print(f"  Diff Decile:   {author['diff_decile']} (1=top 10%, 10=bottom 10%)")
    print(f"  Commit Decile: {author['commit_decile']} (1=top 10%, 10=bottom 10%)")

    # Calculate percentile more precisely
    percentile = (author["rank"] - 1) / total_authors * 100
    print(f"  Percentile:    Top {percentile:.1f}%")

    if author["commits"] > 0:
        avg_diff_per_commit = author["total"] / author["commits"]
        print(f"  Avg Diff/Commit: {avg_diff_per_commit:.0f} lines")

    print()


def _print_author_stats_header(config: GitAnalysisConfig) -> None:
    analysis_type = "merged commits" if config.merged_only else "commits"
    print(f"Author Stats for '{config.author_query}' ({analysis_type})")
    start_date_str = config.start_date.isoformat() if config.start_date else "N/A"
    end_date_str = config.end_date.isoformat() if config.end_date else "N/A"
    print(f"Analysis period: {start_date_str} to {end_date_str}")
    print()

def _print_multiple_author_warning(num_matches: int) -> None:
    logger.warning(f"Found {num_matches} matching authors:")
    print()

def _display_author_specific_stats(
    config: GitAnalysisConfig, author_stats: List[Dict[str, Any]]
) -> int:
    if config.use_current_user:
        logger.info(
            f"Looking up stats for current user: {config.current_user_name} <{config.current_user_email}>"
        )

    author_matches = _get_matching_authors(config, author_stats)

    if not author_matches:
        _log_no_author_matches(config)
        return 1

    print()
    _print_author_stats_header(config)

    if len(author_matches) > 1:
        _print_multiple_author_warning(len(author_matches))

    for author in author_matches:
        _print_author_stats_detail(author, len(author_matches))
    return 0


def _display_ranking_table(
    config: GitAnalysisConfig, author_list: List[Dict[str, Any]]
) -> None:
    print()
    print("Git Author Ranking by Diff Size")
    print(config.get_analysis_description())
    print()

    headers = [
        "Rank",
        "Author",
        "Lines Added",
        "Lines Deleted",
        "Total Diff",
        "Commits",
        "Diff D",
        "Comm D",
    ]
    table_data = []
    for author in author_list:
        author_display = f"{author['author_name']} <{author['author_email']}>"
        if len(author_display) > 45:
            author_display = author_display[:42] + "..."

        added_str = str(author["added"]) if author["added"] > 0 else "-"
        deleted_str = str(author["deleted"]) if author["deleted"] > 0 else "-"

        table_data.append(
            [
                author["rank"],
                author_display,
                added_str,
                deleted_str,
                author["total"],
                author["commits"],
                author["diff_decile"],
                author["commit_decile"],
            ]
        )

    print(_format_table_with_tabulate(headers, table_data))


def _get_min_max_values(
    filtered_authors: List[Dict[str, Any]], decile_key: str
) -> tuple[Any, Any]:
    if decile_key == "diff_decile":
        min_val = min(a["total"] for a in filtered_authors)
        max_val = max(a["total"] for a in filtered_authors)
    else:  # commit_decile
        min_val = min(a["commits"] for a in filtered_authors)
        max_val = max(a["commits"] for a in filtered_authors)
    return min_val, max_val


def _print_single_decile_distribution(
    title: str, range_label: str, decile_key: str, author_list: List[Dict[str, Any]]
) -> None:
    print(f"\n{title}:")
    headers = ["Decile", range_label, "Authors"]
    table_data = []

    for decile in range(1, 11):
        filtered_authors = [a for a in author_list if a[decile_key] == decile]
        if filtered_authors:
            min_val, max_val = _get_min_max_values(filtered_authors, decile_key)
            range_str = (
                f"{min_val:,}-{max_val:,}" if min_val != max_val else f"{min_val:,}"
            )
            table_data.append([decile, range_str, len(filtered_authors)])

    print(_format_table_with_tabulate(headers, table_data))


def _print_decile_distribution(author_list: List[Dict[str, Any]]) -> None:
    _print_single_decile_distribution(
        "Diff Size Decile Distribution", "Diff Size Range", "diff_decile", author_list
    )
    _print_single_decile_distribution(
        "Commit Count Decile Distribution", "Commit Range", "commit_decile", author_list
    )


def _print_summary(
    config: GitAnalysisConfig, author_list: List[Dict[str, Any]]
) -> None:
    print("\nSummary:")
    print("- Ranking based on total lines changed (additions + deletions)")
    print("- Diff D = Diff Size Decile (1=top 10%, 10=bottom 10%)")
    print("- Comm D = Commit Count Decile (1=top 10%, 10=bottom 10%)")
    start_date_str = config.start_date.isoformat() if config.start_date else "N/A"
    end_date_str = config.end_date.isoformat() if config.end_date else "N/A"
    print(f"- Analysis period: from {start_date_str} to {end_date_str}")
    print(f"- Total unique authors: {len(author_list)}")


def _display_full_ranking(
    config: GitAnalysisConfig,
    author_list: List[Dict[str, Any]],
    output_format: OutputFormat,
) -> int:
    if not author_list:
        start_date_str = config.start_date.isoformat() if config.start_date else "N/A"
        end_date_str = config.end_date.isoformat() if config.end_date else "N/A"
        logger.warning(
            f"No commits found in the specified time period: {start_date_str} to {end_date_str}."
        )
        return 0 # Return 0 even if no authors, as it's a successful empty result

    if output_format == OutputFormat.MARKDOWN:
        # Prepare data for Markdown table
        headers = [
            "Rank",
            "Author",
            "Lines Added",
            "Lines Deleted",
            "Total Diff",
            "Commits",
            "Diff D",
            "Comm D",
        ]
        table_data = []
        for author in author_list:
            author_display = f"{author['author_name']} <{author['author_email']}>"
            added_str = str(author["added"]) if author["added"] > 0 else "-"
            deleted_str = str(author["deleted"]) if author["deleted"] > 0 else "-"

            table_data.append(
                {
                    "Rank": author["rank"],
                    "Author": author_display,
                    "Lines Added": added_str,
                    "Lines Deleted": deleted_str,
                    "Total Diff": author["total"],
                    "Commits": author["commits"],
                    "Diff D": author["diff_decile"],
                    "Comm D": author["commit_decile"],
                }
            )
        df = pd.DataFrame(table_data, columns=headers)
        print(format_as_markdown_table(df))

    else:  # Default to TABLE format
        _display_ranking_table(config, author_list)
        _print_decile_distribution(author_list)
        _print_summary(config, author_list)
    return 0
