import logging
import tempfile
import datetime
from typing import Optional
import sys
import re

from dulwich.repo import Repo
from dulwich.client import HttpGitClient
from tqdm import tqdm

from .commit_walker import DulwichCommitWalker
from .diff_parser import DulwichDiffParser

logger = logging.getLogger(__name__)


class DulwichRepoHandler:
    """
    Handles interactions with local and remote Dulwich repositories.
    """

    def __init__(
        self,
        remote_url: str,
        remote_branch: str,
        is_local_repo: bool,
        repo: Optional[Repo],
        commit_walker: DulwichCommitWalker,
    ):
        self.remote_url = remote_url
        self.remote_branch = remote_branch
        self.is_local_repo = is_local_repo
        self.repo = repo
        self.commit_walker = commit_walker

    def handle_local_repo(
        self,
        since_dt: Optional[datetime.datetime],
        until_dt: Optional[datetime.datetime],
        author: Optional[str],
        grep: Optional[str],
        diff_parser: DulwichDiffParser,
    ) -> str:
        repo = self.repo
        if repo is None:
            raise ValueError("Local repository not initialized.")
        logger.info(
            f"Using Dulwich backend for local repository at {self.remote_url}/{self.remote_branch}"
        )
        logger.debug(
            f"Inside get_raw_log_output (local repo): repo.head = {repo.head().hex()}"
        )
        _disable_tqdm = (
            not sys.stdout.isatty() or not sys.stderr.isatty()
        ) or logger.level > logging.INFO
        with tqdm(
            disable=True, file=sys.stderr
        ) as pbar_dummy:  # Always disabled for local repo
            return self.commit_walker.walk_commits(
                repo,
                since_dt,
                until_dt,
                author,
                grep,
                diff_parser,
                pbar_dummy,
            )

    def handle_remote_repo(
        self,
        since_dt: Optional[datetime.datetime],
        until_dt: Optional[datetime.datetime],
        author: Optional[str],
        grep: Optional[str],
        diff_parser: DulwichDiffParser,
    ) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Repo.init(tmpdir)
            client = HttpGitClient(self.remote_url)

            _disable_tqdm = (
                not sys.stdout.isatty() or not sys.stderr.isatty()
            ) or logger.level > logging.INFO

            # Create a single tqdm instance for overall progress
            with tqdm(
                total=0,  # Will be updated dynamically
                unit="obj",
                desc=f"Fetching {self.remote_branch} from {self.remote_url}",
                disable=_disable_tqdm,
                mininterval=0.5,
                leave=True,  # Keep the final bar visible
                dynamic_ncols=True,
                file=sys.stderr,
            ) as pbar:

                def determine_wants_func(
                    refs: dict[bytes, bytes], depth: Optional[int] = None
                ) -> list[bytes]:
                    head_sha = refs.get(b"HEAD")
                    if head_sha:
                        return [head_sha]
                    try:
                        return [
                            refs[f"refs/heads/{self.remote_branch}".encode("utf-8")]
                        ]
                    except KeyError:
                        logger.error(
                            f"Branch '{self.remote_branch}' not found in remote refs."
                        )
                        raise

                def dulwich_progress_callback(progress_bytes: bytes) -> None:
                    message = progress_bytes.decode("utf-8", errors="ignore").strip()
                    if not message:
                        return

                    # Regex to capture progress for "Receiving objects", "Compressing objects", "Counting objects"
                    match_progress = re.match(r".*\s+(\d+)%\s+\((\d+)/(\d+)\)", message)
                    if match_progress:
                        current, total = int(match_progress.group(2)), int(match_progress.group(3))
                        if pbar.total == 0:
                            pbar.total = total
                        pbar.n = current
                        pbar.set_description(f"Fetching {self.remote_branch} from {self.remote_url}: {message}")
                        pbar.refresh()
                        return

                    # Regex to capture total objects from "Total" message
                    match_total = re.match(r"Total (\d+)", message)
                    if match_total:
                        total_objects = int(match_total.group(1))
                        if pbar.total == 0:
                            pbar.total = total_objects
                        pbar.set_description(f"Fetching {self.remote_branch} from {self.remote_url}: {message}")
                        pbar.refresh()
                        return

                    # Fallback for other messages, just update description
                    pbar.set_description(f"Fetching {self.remote_branch} from {self.remote_url}: {message}")
                    pbar.refresh()

                _dulwich_progress_callback = None
                if not _disable_tqdm:
                    _dulwich_progress_callback = dulwich_progress_callback

                logger.info(
                    f"Fetching entire history of branch '{self.remote_branch}' from {self.remote_url}..."
                )
                fetch_result = client.fetch(
                    self.remote_url,
                    repo,
                    determine_wants=determine_wants_func,
                    progress=_dulwich_progress_callback,
                )
                remote_refs = fetch_result.refs

                branch_ref = f"refs/heads/{self.remote_branch}".encode("utf-8")
                if branch_ref not in remote_refs:
                    raise ValueError(
                        f"Branch '{self.remote_branch}' not found in remote repository."
                    )

                head_sha = remote_refs[branch_ref]
                assert head_sha is not None  # Ensure head_sha is not None
                repo.refs[f"refs/heads/{self.remote_branch}".encode("utf-8")] = (
                    head_sha  # Set the branch ref
                )
                repo.refs.set_symbolic_ref(
                    b"HEAD", f"refs/heads/{self.remote_branch}".encode("utf-8")
                )  # Set HEAD to the branch

                # Pass the overall pbar to _walk_commits
                return self.commit_walker.walk_commits(
                    repo,
                    since_dt,
                    until_dt,
                    author,
                    grep,
                    diff_parser,
                    pbar,
                )
