import tempfile
import shutil
from dulwich.repo import Repo
from dulwich.client import HttpGitClient
from dulwich.objects import Commit

remote_url = "https://github.com/python/cpython"
branch_name = "3.14"

# Create a temporary directory for the repository
with tempfile.TemporaryDirectory() as tmpdir:
    print(f"Created temporary directory: {tmpdir}")
    # Initialize an empty repository in the temporary directory
    repo = Repo.init(tmpdir)

    # Create an HttpGitClient, passing the remote_url as base_url
    client = HttpGitClient(remote_url)

    # Fetch from the remote
    # The first argument is the remote URL, the second is the local repository object.
    fetch_result = client.fetch(remote_url, repo)
    remote_refs = fetch_result.refs

    # Find the SHA of the remote branch
    branch_ref = f"refs/heads/{branch_name}".encode('utf-8')
    if branch_ref not in remote_refs:
        print(f"Error: Branch '{branch_name}' not found in remote repository.")
        exit(1)

    head_sha = remote_refs[branch_ref]
    print(f"Head SHA of branch '{branch_name}': {head_sha.hex()}")

    # Get the commit object
    commit = repo.get_object(head_sha)

    if isinstance(commit, Commit):
        print(f"Commit Message: {commit.message.decode('utf-8').strip()}")
    else:
        print(f"Error: Fetched object is not a commit: {type(commit)}")

print(f"Temporary directory {tmpdir} automatically cleaned up.")
