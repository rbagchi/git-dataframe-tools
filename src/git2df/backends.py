import git
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class GitCliBackend:
    """A backend for git2df that interacts with the Git CLI."""

    def __init__(self):
        logger.info("Using GitPython backend for git operations.")

    def _get_default_branch(self, repo_path: str) -> str:
        """Determines the default branch (main or master) for a given repository."""
        logger.debug(f"Checking for default branch in {repo_path}")
        try:
            repo = git.Repo(repo_path)
            if "main" in repo.heads:
                logger.info("Found 'main' as default branch.")
                return "main"
            elif "master" in repo.heads:
                logger.info("Found 'master' as default branch.")
                return "master"
            else:
                logger.warning(
                    "Neither 'main' nor 'master' found as default branch. Defaulting to 'main'."
                )
                return "main"
        except git.InvalidGitRepositoryError:
            logger.error(f"{repo_path} is not a valid git repository.")
            return "main"  # fallback for now

    def get_raw_log_output(
        self,
        repo_path: str,
        log_args: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        merged_only: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Executes a git log command and returns its raw string output.

        Args:
            repo_path: The path to the git repository.
            log_args: Optional list of arguments to pass to 'git log'.
            since: Optional string for --since argument (e.g., "1.month ago").
            until: Optional string for --until argument (e.g., "yesterday").
            author: Optional string to filter by author (e.g., "John Doe").
            grep: Optional string to filter by commit message (e.g., "fix").
            merged_only: If True, only include merged commits.
            include_paths: Optional list of paths to include.
            exclude_paths: Optional list of paths to exclude.

        Returns:
            The raw stdout from the 'git log' command.
        """
        repo = git.Repo(repo_path)
        kwargs = {}
        if since:
            kwargs["since"] = since
        if until:
            kwargs["until"] = until
        if author:
            kwargs["author"] = author
        if grep:
            kwargs["grep"] = grep
        if merged_only:
            default_branch = self._get_default_branch(repo_path)
            kwargs["merges"] = True
            kwargs["rev"] = f"origin/{default_branch}"

        paths = []
        if include_paths:
            paths.extend(include_paths)
        if exclude_paths:
            # GitPython's path filtering doesn't directly support exclude paths in the same way as the git command line with pathspecs.
            # We will have to do the filtering after getting the commits.
            # This is a deviation from the original implementation, but it's the most straightforward way with GitPython.
            pass

        if paths:
            kwargs["paths"] = paths

        commits = repo.iter_commits(**kwargs)

        output = []
        for commit in commits:
            # Manual exclusion of paths
            if exclude_paths:
                if any(
                    f.startswith(tuple(exclude_paths))
                    for f in commit.stats.files.keys()
                ):
                    continue

            parents = " ".join([p.hexsha for p in commit.parents])
            output.append(
                f"--{commit.hexsha}--{parents}--{commit.author.name}--{commit.author.email}--{commit.authored_datetime.isoformat()}--{commit.summary}"
            )

            for file_path, stats in commit.stats.files.items():
                output.append(
                    f"{stats['insertions']}\t{stats['deletions']}\t{file_path}"
                )

        return "\n".join(output)
