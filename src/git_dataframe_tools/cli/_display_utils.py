import logging
from typing import Any, Dict, List

from git_dataframe_tools.config_models import GitAnalysisConfig, print_header

logger = logging.getLogger(__name__)


def _display_author_specific_stats(
    config: GitAnalysisConfig, author_stats: List[Dict[str, Any]]
) -> int:
    if config.use_current_user:
        logger.info(
            f"Looking up stats for current user: {config.current_user_name} <{config.current_user_email}>"
        )

    author_query_lower = config.author_query.lower() if config.author_query else ""
    author_matches = [
        a
        for a in author_stats
        if author_query_lower in a["author_name"].lower()
        or author_query_lower in a["author_email"].lower()
    ]

    if not author_matches:
        analysis_type = "merged commits" if config.merged_only else "commits"
        logger.warning(f"No {analysis_type} found in the specified time period.")
        logger.error(f"No authors found matching '{config.author_query}'")
        print(
            "Suggestion: Try a partial match like first name, last name, or email domain."
        )
        return 1

    print()
    analysis_type = "merged commits" if config.merged_only else "commits"
    print_header(f"Author Stats for '{config.author_query}' ({analysis_type})")
    start_date_str = config.start_date.isoformat() if config.start_date else "N/A"
    end_date_str = config.end_date.isoformat() if config.end_date else "N/A"
    print_header(f"Analysis period: {start_date_str} to {end_date_str}")
    print()

    if len(author_matches) > 1:
        logger.warning(f"Found {len(author_matches)} matching authors:")
        print()

    for author in author_matches:
        logger.info(f"Author: {author['author_name']} <{author['author_email']}>")
        print(f"  Rank:          #{author['rank']} of {len(author_matches)} authors")
        print(f"  Lines Added:   {author['added']:,}")
        print(f"  Lines Deleted: {author['deleted']:,}")
        print(f"  Total Diff:    {author['total']:,}")
        print(f"  Commits:       {author['commits']}")
        print(f"  Diff Decile:   {author['diff_decile']} (1=top 10%, 10=bottom 10%)")
        print(f"  Commit Decile: {author['commit_decile']} (1=top 10%, 10=bottom 10%)")

        # Calculate percentile more precisely
        percentile = (author["rank"] - 1) / len(author_matches) * 100
        print(f"  Percentile:    Top {percentile:.1f}%")

        if author["commits"] > 0:
            avg_diff_per_commit = author["total"] / author["commits"]
            print(f"  Avg Diff/Commit: {avg_diff_per_commit:.0f} lines")

        print()
    return 0


def _display_full_ranking(
    config: GitAnalysisConfig, author_list: List[Dict[str, Any]]
) -> int:
    print()
    print_header("Git Author Ranking by Diff Size")
    print_header(config.get_analysis_description())
    print()

    if not author_list:
        start_date_str = config.start_date.isoformat() if config.start_date else "N/A"
        end_date_str = config.end_date.isoformat() if config.end_date else "N/A"
        logger.warning(
            f"No commits found in the specified time period: {start_date_str} to {end_date_str}."
        )
        return 1

    # Print table header
    print(
        f"{'Rank':>4} {'Author':<45} {'Lines Added':>11} {'Lines Deleted':>12} {'Total Diff':>11} {'Commits':>7} {'Diff D':>6} {'Comm D':>6}"
    )
    print(
        f"{'-'*4:>4} {'-'*45:<45} {'-'*11:>11} {'-'*12:>12} {'-'*11:>11} {'-'*7:>7} {'-'*6:>6} {'-'*6:>6}"
    )

    # Print results
    for author in author_list:
        author_display = f"{author['author_name']} <{author['author_email']}>"
        # Truncate author display if too long
        if len(author_display) > 45:
            author_display = author_display[:42] + "..."

        added_str = str(author["added"]) if author["added"] > 0 else "-"
        deleted_str = str(author["deleted"]) if author["deleted"] > 0 else "-"

        print(
            f"{author['rank']:>4} {author_display:<45} {added_str:>11} {deleted_str:>12} {author['total']:>11} {author['commits']:>7} {author['diff_decile']:>6} {author['commit_decile']:>6}"
        )

    # Print decile distribution summary
    print("\nDiff Size Decile Distribution:")
    print(f"{'Decile':>6} {'Diff Size Range':>25} {'Authors':>8}")
    print(f"{'-'*6:>6} {'-'*25:>25} {'-'*8:>8}")

    for decile in range(1, 11):
        diff_authors = [a for a in author_list if a["diff_decile"] == decile]
        if diff_authors:
            min_diff = min(a["total"] for a in diff_authors)
            max_diff = max(a["total"] for a in diff_authors)
            diff_range = (
                f"{min_diff:,}-{max_diff:,}"
                if min_diff != max_diff
                else f"{min_diff:,}"
            )
            print(f"{decile:>6} {diff_range:>25} {len(diff_authors):>8}")

    print("\nCommit Count Decile Distribution:")
    print(f"{'Decile':>6} {'Commit Range':>15} {'Authors':>8}")
    print(f"{'-'*6:>6} {'-'*15:>15} {'-'*8:>8}")

    for decile in range(1, 11):
        commit_authors = [a for a in author_list if a["commit_decile"] == decile]
        if commit_authors:
            min_commits = min(a["commits"] for a in commit_authors)
            max_commits = max(a["commits"] for a in commit_authors)
            commit_range = (
                f"{min_commits}-{max_commits}"
                if min_commits != max_commits
                else f"{min_commits}"
            )
            print(f"{decile:>6} {commit_range:>15} {len(commit_authors):>8}")

    print("\nSummary:")
    print("- Ranking based on total lines changed (additions + deletions)")
    print("- Diff D = Diff Size Decile (1=top 10%, 10=bottom 10%)")
    print("- Comm D = Commit Count Decile (1=top 10%, 10=bottom 10%)")
    start_date_str = config.start_date.isoformat() if config.start_date else "N/A"
    end_date_str = config.end_date.isoformat() if config.end_date else "N/A"
    print(f"- Analysis period: from {start_date_str} to {end_date_str}")
    print(f"- Total unique authors: {len(author_list)}")
    return 0
