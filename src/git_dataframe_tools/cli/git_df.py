import logging
import os
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import typer
from typing_extensions import Annotated

from git2df import get_commits_df
from git_dataframe_tools.cli.common_args import (
    Author,
    Debug,
    ExcludePath,
    Grep,
    Merges,
    Path,
    RemoteBranch,
    RemoteUrl,
    RepoPath,
    Since,
    Until,
    Verbose,
)
from git_dataframe_tools.git_python_repo_info_provider import GitPythonRepoInfoProvider
from git_dataframe_tools.logger import setup_logging

DATA_VERSION = "1.0"  # Major version of the data format

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="Extracts filtered Git commit data and saves it to a Parquet file as a Pandas DataFrame."
)


def _validate_and_setup_paths(
    repo_path: str, remote_url: Optional[str], remote_branch: str
) -> str:
    if not remote_url and repo_path and not os.path.isdir(repo_path):
        logger.error(
            f"Repository path '{repo_path}' does not exist or is not a directory."
        )
        raise typer.Exit(1)

    if remote_url:
        logger.info(
            f"Extracting commit data from remote '{remote_url}' branch '{remote_branch}'..."
        )
        return "."  # Use current directory as a placeholder for remote operations
    else:
        logger.info(f"Extracting commit data from local '{repo_path}'...")
        return repo_path


def _handle_empty_dataframe(output: str, repo_path: str) -> None:
    logger.warning(f"No commits found for the specified criteria in '{repo_path}'.")
    try:
        empty_df = pd.DataFrame()
        table = pa.Table.from_pandas(empty_df)
        custom_metadata = {
            "data_version": DATA_VERSION,
            "description": "Git commit data extracted by git-df CLI",
        }
        metadata_bytes = {
            k.encode(): str(v).encode() for k, v in custom_metadata.items()
        }

        temp_table = pa.Table.from_pandas(empty_df)
        new_schema = temp_table.schema.with_metadata(metadata_bytes)

        table = pa.Table.from_pandas(empty_df, schema=new_schema)
        pq.write_table(table, output)
        logger.info(
            f"Created empty Parquet file at '{output}' as no commits were found."
        )
    except Exception as e:
        logger.error(f"Error creating empty Parquet file: {e}")
        raise typer.Exit(1)


def _save_dataframe_to_parquet(commits_df: pd.DataFrame, output: str) -> None:
    logger.info(f"Saving {len(commits_df)} commits to '{output}'...")
    try:
        table = pa.Table.from_pandas(commits_df)

        custom_metadata = {
            "data_version": DATA_VERSION,
            "description": "Git commit data extracted by git-df CLI",
        }

        metadata_bytes = {
            k.encode(): str(v).encode() for k, v in custom_metadata.items()
        }
        temp_table = pa.Table.from_pandas(commits_df)
        new_schema = temp_table.schema.with_metadata(metadata_bytes)

        table = pa.Table.from_pandas(commits_df, schema=new_schema)

        pq.write_table(table, output)
        logger.info(f"Successfully saved commit data to '{output}'.")
    except Exception as e:
        logger.error(f"Error saving data to Parquet: {e}")
        raise typer.Exit(1)


@app.command()
def main(
    output: Annotated[
        str,
        typer.Option(
            "-o",
            "--output",
            help='Output Parquet file path (e.g., "commits.parquet")',
        ),
    ],
    repo_path: RepoPath = ".",
    remote_url: RemoteUrl = None,
    remote_branch: RemoteBranch = "main",
    since: Since = None,
    until: Until = None,
    author: Author = None,
    grep: Grep = None,
    merges: Merges = False,
    path: Path = None,
    exclude_path: ExcludePath = None,
    verbose: Verbose = False,
    debug: Debug = False,
):
    setup_logging(debug=debug, verbose=verbose)
    logger.debug(f"CLI arguments: {locals()}")

    repo_path_arg = _validate_and_setup_paths(repo_path, remote_url, remote_branch)

    try:
        repo_info_provider = GitPythonRepoInfoProvider()
        commits_df = get_commits_df(
            repo_path=repo_path_arg,
            remote_url=remote_url,
            remote_branch=remote_branch,
            since=since,
            until=until,
            author=author,
            grep=grep,
            merged_only=merges,
            include_paths=path,
            exclude_paths=exclude_path,
            repo_info_provider=repo_info_provider,
        )
    except Exception as e:
        logger.error(f"Error fetching git log data: {e}")
        raise typer.Exit(1)

    if commits_df.empty:
        _handle_empty_dataframe(output, repo_path)
        return

    _save_dataframe_to_parquet(commits_df, output)


if __name__ == "__main__":
    app()
