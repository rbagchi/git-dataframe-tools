import datetime
from typing import Optional


class DulwichCommitFilters:
    """
    Provides methods for filtering Dulwich commits based on various criteria.
    """

    def filter_commits_by_date(
        self,
        commit_datetime: datetime.datetime,
        since_dt: Optional[datetime.datetime],
        until_dt: Optional[datetime.datetime],
    ) -> bool:
        """
        Filters a commit based on its commit date.

        Args:
            commit_datetime: The datetime object of the commit.
            since_dt: Optional start date for filtering.
            until_dt: Optional end date for filtering.

        Returns:
            True if the commit falls within the specified date range, False otherwise.
        """
        if since_dt and commit_datetime < since_dt:
            return False
        if until_dt and commit_datetime > until_dt:
            return False
        return True

    def filter_commits_by_author_and_grep(
        self, commit_metadata: dict, author: Optional[str], grep: Optional[str]
    ) -> bool:
        """
        Filters a commit based on author and a grep pattern in the commit message summary.

        Args:
            commit_metadata: A dictionary containing commit metadata.
            author: Optional author name or email to filter by.
            grep: Optional string to search for in the commit message summary.

        Returns:
            True if the commit matches the author and grep criteria, False otherwise.
        """
        # Apply author filter
        if (
            author
            and author.lower() not in commit_metadata["author_name"].lower()
            and author.lower() not in commit_metadata["author_email"].lower()
        ):
            # logger.debug( # Logger will be added in the backend.py
            #     f"Skipping commit: author '{author}' not found in '{commit_metadata['author_name']} <{commit_metadata['author_email']}>'"
            # )
            return False

        # Apply grep filter (simplified: check in commit message summary)
        if (
            grep
            and grep.lower() not in commit_metadata["commit_message_summary"].lower()
        ):
            # logger.debug( # Logger will be added in the backend.py
            #     f"Skipping commit: grep '{grep}' not found in '{commit_metadata['commit_message_summary']}'"
            # )
            return False
        return True
