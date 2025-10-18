from typing import Optional, List
from typing_extensions import Annotated
import typer

# Common CLI Arguments

RepoPath = Annotated[
    str,
    typer.Option(
        "--repo-path",
        help="Path to the Git repository (default: current directory). Cannot be used with --remote-url or --df-path.",
    ),
]

RemoteUrl = Annotated[
    Optional[str],
    typer.Option(
        "--remote-url",
        help="URL of the remote Git repository to analyze (e.g., https://github.com/user/repo). Cannot be used with --repo-path or --df-path.",
    ),
]

RemoteBranch = Annotated[
    str,
    typer.Option(
        "--remote-branch",
        help="Branch of the remote repository to analyze (default: main). Only applicable with --remote-url.",
    ),
]

Since = Annotated[
    Optional[str],
    typer.Option(
        "-S",
        "--since",
        help='Start date for analysis (e.g., "2023-01-01", "3 months ago", "1 year ago")',
    ),
]

Until = Annotated[
    Optional[str],
    typer.Option(
        "-U", "--until", help='End date for analysis (e.g., "2023-03-31", "now")'
    ),
]

Author = Annotated[
    Optional[str],
    typer.Option(
        "-a",
        "--author",
        help='Filter by author name or email (e.g., "John Doe", "john@example.com")',
    ),
]

Me = Annotated[
    bool,
    typer.Option(
        "--me",
        help="Filter by the current Git user (based on global Git config)",
    ),
]

Grep = Annotated[
    Optional[str],
    typer.Option(
        "-g", "--grep", help='Filter by commit message (e.g., "fix", "feature")'
    ),
]

Merges = Annotated[
    bool,
    typer.Option(
        "-m",
        "--merges",
        help="Only include commits that are merged into the current branch (e.g., via pull requests)",
    ),
]

Path = Annotated[
    Optional[List[str]],
    typer.Option(
        "-p",
        "--path",
        help="Include only changes in specified paths (can be used multiple times)",
    ),
]

ExcludePath = Annotated[
    Optional[List[str]],
    typer.Option(
        "-x",
        "--exclude-path",
        help="Exclude changes in specified paths (can be used multiple times)",
    ),
]

Verbose = Annotated[
    bool,
    typer.Option("-v", "--verbose", help="Enable verbose output (INFO level)"),
]

Debug = Annotated[
    bool,
    typer.Option("-d", "--debug", help="Enable debug output (DEBUG level)"),
]
