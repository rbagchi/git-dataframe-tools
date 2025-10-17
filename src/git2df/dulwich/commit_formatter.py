import datetime
import logging
from dulwich.objects import Commit

logger = logging.getLogger(__name__)


class DulwichCommitFormatter:
    """
    Provides methods for extracting and formatting commit metadata from Dulwich Commit objects.
    """

    def extract_commit_metadata(self, commit: Commit) -> dict:
        """
        Extracts relevant metadata from a Dulwich Commit object.

        Args:
            commit: The Dulwich Commit object.

        Returns:
            A dictionary containing extracted commit metadata.
        """
        commit_hash = commit.id.hex()
        logger.debug(f"Dulwich Commit hash: {commit_hash}")
        parent_hashes = " ".join([p.hex() for p in commit.parents])
        raw_author = commit.author.decode("utf-8")
        logger.debug(f"Raw author string: {raw_author}")
        author_name = raw_author.split("<")[0].strip()
        author_email = raw_author.split("<")[1].strip(">")
        logger.debug(
            f"Extracted author_name: {author_name}, author_email: {author_email}"
        )
        commit_datetime = datetime.datetime.fromtimestamp(
            commit.commit_time, tz=datetime.timezone.utc
        )
        commit_timestamp = commit.commit_time
        commit_message_summary = (
            commit.message.decode("utf-8").splitlines()[0].replace("--", " ")
        )
        commit_message = commit.message.decode("utf-8")
        return {
            "commit_hash": commit_hash,
            "parent_hashes": parent_hashes,
            "author_name": author_name,
            "author_email": author_email,
            "commit_date": commit_datetime,
            "commit_timestamp": commit_timestamp,
            "commit_message_summary": commit_message_summary,
            "commit_message": commit_message,
        }

    def format_commit_line(self, commit_metadata: dict) -> str:
        """
        Formats extracted commit metadata into a single string line compatible with git2df's parser.

        Args:
            commit_metadata: A dictionary containing extracted commit metadata.

        Returns:
            A formatted string representing the commit.
        """
        formatted_string = f"{commit_metadata['commit_hash']}@@@FIELD@@@"
        formatted_string += f"{commit_metadata['parent_hashes']}@@@FIELD@@@"
        formatted_string += f"{commit_metadata['author_name']}@@@FIELD@@@"
        formatted_string += f"{commit_metadata['author_email']}@@@FIELD@@@"
        formatted_string += f"{commit_metadata['commit_date'].isoformat()}\t{commit_metadata['commit_timestamp']}@@@FIELD@@@"
        formatted_string += (
            f"---MSG_START---{commit_metadata['commit_message']}---MSG_END---"
        )
        return formatted_string
