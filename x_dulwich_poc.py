import tempfile
import datetime
from dulwich.repo import Repo
from dulwich.client import HttpGitClient
from dulwich.objects import Commit
from dulwich.diff_tree import tree_changes

remote_url = "https://github.com/pallets/flask"
branch_name = "main"

# Calculate 'last year' date
one_year_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)

with tempfile.TemporaryDirectory() as tmpdir:
    print(f"Created temporary directory: {tmpdir}")
    
    repo = Repo.init(tmpdir)
    client = HttpGitClient(remote_url)

    print(f"Fetching entire history of branch '{branch_name}' (this may take a moment)...")
    fetch_result = client.fetch(
        remote_url,
        repo,
        determine_wants=lambda refs: [refs[f"refs/heads/{branch_name}".encode('utf-8')]]
    )
    remote_refs = fetch_result.refs

    branch_ref = f"refs/heads/{branch_name}".encode('utf-8')
    if branch_ref not in remote_refs:
        print(f"Error: Branch '{branch_name}' not found")
        exit(1)

    head_sha = remote_refs[branch_ref]
    repo[b"HEAD"] = head_sha

    print(f"Head SHA of branch '{branch_name}': {head_sha.hex()}")

    print(f"\nIterating commits on branch '{branch_name}' since {one_year_ago.date()}:")
    commits_data = []
    for entry in repo.get_walker(include=[head_sha]):
        commit: Commit = entry.commit
        commit_datetime = datetime.datetime.fromtimestamp(commit.commit_time, tz=datetime.timezone.utc)

        if commit_datetime >= one_year_ago:
            commit_hash = commit.id.hex()
            parent_hashes = [p.hex() for p in commit.parents]
            author_name = commit.author.decode('utf-8').split('<')[0].strip()
            author_email = commit.author.decode('utf-8').split('<')[1].strip('>')
            commit_message = commit.message.decode('utf-8').strip()

            file_changes_list = []
            if commit.parents: # Not an initial commit
                parent_commit = repo.get_object(commit.parents[0])
                parent_tree = parent_commit.tree
                current_tree = commit.tree

                for change in tree_changes(repo.object_store, parent_tree, current_tree):
                    change_type = "unknown"
                    if change.type == b"add":
                        change_type = "add"
                    elif change.type == b"delete":
                        change_type = "delete"
                    elif change.type == b"modify":
                        change_type = "modify"
                    elif change.type == b"rename":
                        change_type = "rename"
                    elif change.type == b"copy":
                        change_type = "copy"
                    
                    old_path = change.old.path.decode() if change.old and change.old.path else None
                    new_path = change.new.path.decode() if change.new and change.new.path else None

                    # For additions and deletions, we can get the content of the new/old file
                    # and count lines to estimate additions/deletions.
                    # This is a simplified approach; a full diff would be more complex.
                    additions = 0
                    deletions = 0

                    if change.type == b"add" and change.new and change.new.sha:
                        blob = repo.get_object(change.new.sha)
                        additions = len(blob.as_pretty_string().splitlines())
                    elif change.type == b"delete" and change.old and change.old.sha:
                        blob = repo.get_object(change.old.sha)
                        deletions = len(blob.as_pretty_string().splitlines())
                    elif change.type == b"modify" and change.old and change.new and change.old.sha and change.new.sha:
                        # This is a very basic way to estimate changes, not a true diff stat
                        old_blob = repo.get_object(change.old.sha)
                        new_blob = repo.get_object(change.new.sha)
                        old_lines = old_blob.as_pretty_string().splitlines()
                        new_lines = new_blob.as_pretty_string().splitlines()
                        # A more accurate diff would involve line-by-line comparison
                        additions = len(new_lines) - len(old_lines) if len(new_lines) > len(old_lines) else 0
                        deletions = len(old_lines) - len(new_lines) if len(old_lines) > len(new_lines) else 0

                    file_changes_list.append({
                        'change_type': change_type,
                        'old_path': old_path,
                        'new_path': new_path,
                        'additions': additions,
                        'deletions': deletions
                    })
            
            commits_data.append({
                'commit_hash': commit_hash,
                'parent_hashes': parent_hashes,
                'author_name': author_name,
                'author_email': author_email,
                'commit_date': commit_datetime,
                'commit_message': commit_message,
                'file_changes': file_changes_list
            })
            print(f"  Commit: {commit_hash}")
            print(f"  Author: {author_name} <{author_email}>")
            print(f"  Date:   {commit_datetime}")
            print(f"  Msg:    {commit_message.splitlines()[0]}")
            if file_changes_list:
                print(f"  File Changes ({len(file_changes_list)}):")
                for fc in file_changes_list:
                    print(f"    - {fc['change_type']}: {fc['old_path'] or fc['new_path']} (+{fc['additions']}/-{fc['deletions']})")
            print("-" * 20)
        else:
            break

    print(f"Total commits found within the last year: {len(commits_data)}")
