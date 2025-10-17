import logging
import pandas as pd
from typing import List
from git2df.git_parser import GitLogEntry

logger = logging.getLogger(__name__)


def build_commits_df(parsed_data: List[GitLogEntry]) -> pd.DataFrame:
    """
    Converts parsed git data (list of GitLogEntry objects) into a Pandas DataFrame.

    Args:
        parsed_data: A list of GitLogEntry objects, where each object represents a commit
                     and contains all the extracted commit and file information.

    Returns:
        A Pandas DataFrame with commit-related information, with one row per file change per commit.
    """
    logger.debug(
        f"Building DataFrame from {len(parsed_data)} parsed GitLogEntry objects."
    )
    if not parsed_data:
        logger.info("No parsed data entries, returning empty DataFrame.")
        return pd.DataFrame(
            columns=[
                "commit_hash",
                "parent_hash",
                "author_name",
                "author_email",
                "commit_date",
                "commit_timestamp",
                "commit_message",
                "file_paths",
                "change_type",
                "additions",
                "deletions",
                "old_file_path",
            ]
        )

    records = []
    for entry in parsed_data:
        if entry.file_changes:
            for file_change in entry.file_changes:
                records.append(
                    {
                        "commit_hash": entry.commit_hash,
                        "parent_hash": entry.parent_hash,
                        "author_name": entry.author_name,
                        "author_email": entry.author_email,
                        "commit_date": entry.commit_date,
                        "commit_timestamp": entry.commit_timestamp,
                        "commit_message": entry.commit_message,
                        "file_paths": file_change.file_path,
                        "change_type": file_change.change_type,
                        "additions": file_change.additions,
                        "deletions": file_change.deletions,
                        "old_file_path": file_change.old_file_path,
                    }
                )
                logger.debug(f"Appended record for commit {entry.commit_hash}, file {file_change.file_path}")
        else:
            # Handle commits with no file changes (e.g., merge commits without --numstat output)
            records.append(
                {
                    "commit_hash": entry.commit_hash,
                    "parent_hash": entry.parent_hash,
                    "author_name": entry.author_name,
                    "author_email": entry.author_email,
                    "commit_date": entry.commit_date,
                    "commit_timestamp": entry.commit_timestamp,
                    "commit_message": entry.commit_message,
                    "file_paths": None,  # Or an appropriate default
                    "change_type": None,  # Or an appropriate default
                    "additions": 0,
                    "deletions": 0,
                    "old_file_path": None,
                }
            )

    df = pd.DataFrame(records)
    logger.info(f"Successfully built DataFrame with {len(df)} rows.")
    return df
