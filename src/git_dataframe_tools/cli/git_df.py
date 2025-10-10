import typer
from typing import Optional, List
from typing_extensions import Annotated
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import logging

from git2df import get_commits_df
from git_dataframe_tools.logger import setup_logging

DATA_VERSION = "1.0"  # Major version of the data format

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="Extracts filtered Git commit data and saves it to a Parquet file as a Pandas DataFrame."
)


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
    repo_path: Annotated[
        str,
        typer.Option(
            "--repo-path",
            help="Path to the Git repository (default: current directory). This cannot be used with --remote-url.",
        ),
    ] = ".",
    remote_url: Annotated[
        Optional[str],
        typer.Option(
            "--remote-url",
            help="URL of the remote Git repository to analyze (e.g., https://github.com/user/repo). This cannot be used with --repo-path.",
        ),
    ] = None,
    remote_branch: Annotated[
        str,
        typer.Option(
            "--remote-branch",
            help="Branch of the remote repository to analyze (default: main). Only applicable with --remote-url.",
        ),
    ] = "main",
    since: Annotated[
        Optional[str],
        typer.Option(
            "-S",
            "--since",
            help='Start date for analysis (e.g., "2023-01-01", "3 months ago", "1 year ago")',
        ),
    ] = None,
    until: Annotated[
        Optional[str],
        typer.Option(
            "-U", "--until", help='End date for analysis (e.g., "2023-03-31", "now")'
        ),
    ] = None,
    author: Annotated[
        Optional[str],
        typer.Option(
            "-a",
            "--author",
            help='Filter by author name or email (e.g., "John Doe", "john@example.com")',
        ),
    ] = None,
    grep: Annotated[
        Optional[str],
        typer.Option(
            "-g", "--grep", help='Filter by commit message (e.g., "fix", "feature")'
        ),
    ] = None,
    merges: Annotated[
        bool,
        typer.Option(
            "-m",
            "--merges",
            help="Only include commits that are merged into the current branch (e.g., via pull requests)",
        ),
    ] = False,
    path: Annotated[
        Optional[List[str]],
        typer.Option(
            "-p",
            "--path",
            help="Include only changes in specified paths (can be used multiple times)",
        ),
    ] = None,
    exclude_path: Annotated[
        Optional[List[str]],
        typer.Option(
            "-x",
            "--exclude-path",
            help="Exclude changes in specified paths (can be used multiple times)",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "-v", "--verbose", help="Enable verbose output (INFO level)"
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "-d", "--debug", help="Enable debug output (DEBUG level)"
        ),
    ] = False,
):
    setup_logging(debug=debug, verbose=verbose)
    logger.debug(f"CLI arguments: {locals()}")

    # Ensure the repository path exists if a local repo is used
    if not remote_url and repo_path and not os.path.isdir(repo_path):
        logger.error(
            f"Repository path '{repo_path}' does not exist or is not a directory."
        )
        raise typer.Exit(1)

    if remote_url:
        logger.info(
            f"Extracting commit data from remote '{remote_url}' branch '{remote_branch}'..."
        )
        repo_path_arg = "."  # Use current directory as a placeholder for remote operations
    else:
        logger.info(f"Extracting commit data from local '{repo_path}'...")
        repo_path_arg = repo_path

    try:
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
        )
    except Exception as e:
        logger.error(f"Error fetching git log data: {e}")
        raise typer.Exit(1)

    if commits_df.empty:
        logger.warning(
            f"No commits found for the specified criteria in '{repo_path}'."
        )
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
        return

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


if __name__ == "__main__":
    app()
