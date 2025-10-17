import pytest
from git2df.dulwich.backend import DulwichRemoteBackend
from git2df import get_commits_df
import pandas as pd


def test_remote_fetch():
    # This test requires network access
    backend = DulwichRemoteBackend("https://github.com/pallets/flask", "main")
    # Just fetch, don't get output
    backend.get_log_entries(since="1 day ago")


def test_remote_fetch_stremio_web_development_branch_returns_commits():
    """
    Tests that fetching from a known remote URL and branch (Stremio/stremio-web, development)
    with a reasonable 'since' date returns a non-empty DataFrame.
    """
    remote_url = "https://github.com/Stremio/stremio-web"
    remote_branch = "development"
    since = "6 months ago"  # Use a relative date to ensure it's always recent
    # until = "2025-10-09" # Removed specific until date for broader coverage

    try:
        df = get_commits_df(
            remote_url=remote_url, remote_branch=remote_branch, since=since
        )
    except IndexError as e:
        pytest.fail(
            f"IndexError during commit parsing: {e}. This indicates a problem with author/email format in commit messages."
        )

    assert isinstance(df, pd.DataFrame)
    assert (
        not df.empty
    ), f"No commits fetched from {remote_url}/{remote_branch} within the last {since}"
    assert len(df) > 0, f"Expected more than 0 commits, but got {len(df)}"
    print(
        f"Successfully fetched {len(df)} commits from {remote_url}/{remote_branch} since {since}"
    )
