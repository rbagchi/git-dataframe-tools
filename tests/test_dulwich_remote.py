from git2df.dulwich_backend import DulwichRemoteBackend
from git2df import get_commits_df
import pandas as pd

def test_remote_fetch():
    # This test requires network access
    backend = DulwichRemoteBackend("https://github.com/pallets/flask", "main")
    # Just fetch, don't get output
    backend.get_raw_log_output(since="1 day ago")

def test_remote_fetch_stremio_web_development_branch_returns_commits():
    """
    Tests that fetching from a known remote URL and branch (Stremio/stremio-web, development)
    with a reasonable 'since' date returns a non-empty DataFrame.
    """
    remote_url = "https://github.com/Stremio/stremio-web"
    remote_branch = "development"
    since = "2025-04-09"
    until = "2025-10-09"

    df = get_commits_df(
        remote_url=remote_url,
        remote_branch=remote_branch,
        since=since,
        until=until
    )

    assert isinstance(df, pd.DataFrame)
    assert not df.empty, f"No commits fetched from {remote_url}/{remote_branch} between {since} and {until}"
    assert len(df) == 1904, f"Expected 1904 commits, but got {len(df)}"
    print(f"Successfully fetched {len(df)} commits from {remote_url}/{remote_branch}")
