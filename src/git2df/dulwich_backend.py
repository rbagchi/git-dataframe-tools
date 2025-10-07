import logging
import tempfile
import datetime
import shutil
from typing import List, Optional, Any

from dulwich.repo import Repo
from dulwich.client import HttpGitClient
from dulwich.objects import Commit
from dulwich.diff_tree import TreeChange
import dulwich.diff_tree

logger = logging.getLogger(__name__)


class DulwichRemoteBackend:
    """A backend for git2df that interacts with remote Git repositories using Dulwich."""

    def __init__(self, remote_url: str, remote_branch: str = "main"):
        self.remote_url = remote_url
        self.remote_branch = remote_branch
        logger.info(f"Using Dulwich backend for remote operations on {remote_url}/{remote_branch}")

    def get_raw_log_output(
        self,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False, # Not directly supported by dulwich fetch by date
        include_paths: Optional[List[str]] = None, # Will be filtered post-fetch
        exclude_paths: Optional[List[str]] = None, # Will be filtered post-fetch
    ) -> str:
        """
        Fetches git log information from a remote repository using Dulwich and returns it
        in a raw string format compatible with git2df's parser.
        """
        output_lines = []

        # Convert since/until to datetime objects for filtering
        since_dt = None
        if since:
            # This is a simplified parsing. A robust solution would use a proper date parser.
            try:
                # Assuming 'since' is in a format like '1 year ago', '1 month ago', etc.
                # For now, we'll just use the 'last year' logic from the PoC.
                # This needs to be improved for full compatibility with git2df's date parsing.
                if "year" in since:
                    num_years = int(since.split(' ')[0])
                    since_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=num_years * 365)
                elif "month" in since:
                    num_months = int(since.split(' ')[0])
                    since_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=num_months * 30) # Approximation
                elif "day" in since:
                    num_days = int(since.split(' ')[0])
                    since_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=num_days)
                else:
                    logger.warning(f"Unsupported 'since' format: {since}. Using last year as default.")
                    since_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
            except Exception as e:
                logger.error(f"Error parsing 'since' date '{since}': {e}. Using last year as default.")
                since_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)
        else:
            # Default to last year if no 'since' is provided, matching the PoC
            since_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)

        # Dulwich operations require a temporary local repository
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Repo.init(tmpdir)
            client = HttpGitClient(self.remote_url)

            logger.info(f"Fetching entire history of branch '{self.remote_branch}' from {self.remote_url}...")
            fetch_result = client.fetch(
                self.remote_url,
                repo,
                determine_wants=lambda refs: [refs[f"refs/heads/{self.remote_branch}".encode('utf-8')]]
            )
            remote_refs = fetch_result.refs

            branch_ref = f"refs/heads/{self.remote_branch}".encode('utf-8')
            if branch_ref not in remote_refs:
                raise ValueError(f"Branch '{self.remote_branch}' not found in remote repository.")

            head_sha = remote_refs[branch_ref]
            repo[b"HEAD"] = head_sha

            logger.info(f"Iterating commits on branch '{self.remote_branch}' since {since_dt.date() if since_dt else 'beginning of time'}:")
            
            for entry in repo.get_walker(include=[head_sha]):
                commit: Commit = entry.commit
                commit_datetime = datetime.datetime.fromtimestamp(commit.commit_time, tz=datetime.timezone.utc)
                logger.debug(f"Processing commit {commit.id.hex()} with date {commit_datetime}")

                if since_dt and commit_datetime < since_dt:
                    logger.debug(f"Breaking loop: commit date {commit_datetime} is older than since_dt {since_dt}")
                    break # Stop if commit is older than 'since_dt'
                
                # Apply 'until' filter if provided
                until_dt = None
                if until:
                    # Simplified parsing for 'until' as well
                    try:
                        if "yesterday" in until:
                            until_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
                        else:
                            logger.warning(f"Unsupported 'until' format: {until}. Ignoring.")
                    except Exception as e:
                        logger.error(f"Error parsing 'until' date '{until}': {e}. Ignoring.")
                
                if until_dt and commit_datetime > until_dt:
                    logger.debug(f"Skipping commit: commit date {commit_datetime} is newer than until_dt {until_dt}")
                    continue # Skip if commit is newer than 'until_dt'

                # Apply author filter
                if author and author.lower() not in commit.author.decode('utf-8').lower():
                    logger.debug(f"Skipping commit: author '{author}' not found in '{commit.author.decode('utf-8')}'")
                    continue

                # Apply grep filter (simplified: check in commit message summary)
                if grep and grep.lower() not in commit.message.decode('utf-8').lower():
                    logger.debug(f"Skipping commit: grep '{grep}' not found in '{commit.message.decode('utf-8')}'")
                    continue

                commit_hash = commit.id.hex()
                parent_hashes = " ".join([p.hex() for p in commit.parents])
                author_name = commit.author.decode('utf-8').split('<')[0].strip()
                author_email = commit.author.decode('utf-8').split('<')[1].strip('>')
                commit_message_summary = commit.message.decode('utf-8').splitlines()[0].replace("--", " ")

                output_lines.append(
                    f"---{commit_hash}---{parent_hashes}---{author_name}---{author_email}---{commit_datetime.isoformat()}---{commit_message_summary}"
                )
                logger.debug(f"Appended commit line for {commit_hash}")

                # Extract file changes
                old_tree_id = None
                if commit.parents: # Not an initial commit
                    parent_commit = repo.get_object(commit.parents[0])
                    old_tree_id = parent_commit.tree
                    current_tree = commit.tree # This variable is not used in the raw_changes line

                raw_changes = dulwich.diff_tree.tree_changes(repo.object_store, old_tree_id, commit.tree)



                for change in raw_changes:
                    change_type = change.type
                    old_path = change.old.path if change.old else None
                    new_path = change.new.path if change.new else None
                    old_mode = change.old.mode if change.old else None
                    new_mode = change.new.mode if change.new else None
                    old_sha = change.old.sha if change.old else None
                    new_sha = change.new.sha if change.new else None
                    # Determine the path based on change type
                    path = new_path.decode("utf-8") if new_path else (old_path.decode("utf-8") if old_path else "")

                    # Apply include_paths and exclude_paths filters
                    if include_paths and path and not any(path.startswith(p) for p in include_paths):
                        continue
                    if exclude_paths and path and any(path.startswith(p) for p in exclude_paths):
                        continue

                    # Simplified size and hash for now, as dulwich.diff_tree.tree_changes doesn't directly provide them
                    # A more robust solution would involve looking up blob objects
                    size = 0 # Placeholder
                    hash_val = "" # Placeholder

                    additions = 0
                    deletions = 0

                    # Calculate additions and deletions based on change_type and blob content
                    if change_type == b"add" and new_sha:
                        blob = repo.get_object(new_sha)
                        additions = len(blob.as_pretty_string().splitlines())
                    elif change_type == b"delete" and old_sha:
                        blob = repo.get_object(old_sha)
                        deletions = len(blob.as_pretty_string().splitlines())
                    elif change_type == b"modify" and old_sha and new_sha:
                        old_blob = repo.get_object(old_sha)
                        new_blob = repo.get_object(new_sha)
                        old_lines = old_blob.as_pretty_string().splitlines()
                        new_lines = new_blob.as_pretty_string().splitlines()
                        additions = len(new_lines) - len(old_lines) if len(new_lines) > len(old_lines) else 0
                        deletions = len(old_lines) - len(new_lines) if len(old_lines) > len(new_lines) else 0

                    output_lines.append(
                        f"{additions}\t{deletions}\t{path}"
                    )

        logger.debug(f"Final output_lines: {output_lines}")
        return "\n".join(output_lines)


