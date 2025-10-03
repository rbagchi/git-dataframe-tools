import logging
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def build_commits_df(parsed_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converts parsed git data (list of commit dictionaries) into a Pandas DataFrame.

    Args:
        parsed_data: A list of dictionaries, where each dictionary represents a commit
                     and contains all the extracted commit and file information.

    Returns:
        A Pandas DataFrame with commit-related information, with one row per file change per commit.
    """
    logger.debug(f"Building DataFrame from {len(parsed_data)} parsed data entries.")
    if not parsed_data:
        logger.info("No parsed data entries, returning empty DataFrame.")
        return pd.DataFrame(
            columns=[
                "commit_hash",
                "parent_hash",
                "author_name",
                "author_email",
                "commit_date",
                "commit_message",
                "file_paths",
                "change_type",
                "additions",
                "deletions",
            ]
        )

    df = pd.DataFrame(parsed_data)
    logger.info(f"Successfully built DataFrame with {len(df)} rows.")
    return df
