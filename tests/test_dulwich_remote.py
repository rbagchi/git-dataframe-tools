import pytest
from git2df.dulwich_backend import DulwichRemoteBackend
from datetime import datetime, timezone

def test_remote_fetch():
    # This test requires network access
    backend = DulwichRemoteBackend("https://github.com/pallets/flask", "main")
    # Just fetch, don't get output
    backend.get_raw_log_output(since="1 day ago")
