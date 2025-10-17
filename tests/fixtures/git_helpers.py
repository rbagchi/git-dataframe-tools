from pathlib import Path
import pygit2

def _handle_file_changes(repo, repo_path, commit_data):
    for filename, content in commit_data["files"].items():
        file_path = Path(repo_path) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        repo.index.add(str(filename))

def _handle_file_deletions(repo, repo_path, commit_data):
    if "delete_files" in commit_data:
        for filename in commit_data["delete_files"]:
            file_path = Path(repo_path) / filename
            if file_path.exists():
                file_path.unlink()
            repo.index.remove(str(filename))

def _handle_file_renames(repo, repo_path, commit_data):
    if "rename_files" in commit_data:
        for old_name, new_name in commit_data["rename_files"]:
            old_file_path = Path(repo_path) / old_name
            
            if old_file_path.exists():
                old_file_path.unlink()
            repo.index.remove(str(old_name))
            repo.index.add(str(new_name)) # Assume new file content is handled by _handle_file_changes or is a pure rename

def _create_merge_commit(repo, current_author, current_committer, commit_data, repo_path):
    # Create a new branch for the merge
    branch_name = commit_data["merge_branch"]
    main_branch_ref = repo.lookup_reference("refs/heads/main")
    main_commit = repo[main_branch_ref.target]
    
    repo.create_branch(branch_name, main_commit)
    
    # Commit to the new branch
    repo.head.set_target(repo.lookup_reference(f"refs/heads/{branch_name}").target)
    _handle_file_changes(repo, repo_path, commit_data)
    repo.index.write()
    tree = repo.index.write_tree()
    branch_commit_oid = repo.create_commit(
        f"refs/heads/{branch_name}",
        current_author,
        current_committer,
        f"Commit on {branch_name}",
        tree,
        [repo.head.target],
    )
    feature_commit = repo[branch_commit_oid]

    # Switch back to main
    repo.head.set_target(main_branch_ref.target)

    # Perform the merge
    merge_result = repo.merge_commits(main_commit, feature_commit)
    
    if merge_result is None:
        raise Exception("Merge was not needed, but expected to be.")
    
    # Check for conflicts (optional, but good practice)
    if repo.index.conflicts:
        raise Exception("Merge conflicts detected during test setup!")

    # Write the merged tree
    repo.index.write()
    merged_tree = repo.index.write_tree()

    # Create the merge commit
    repo.create_commit(
        "refs/heads/main",
        current_author,
        current_committer,
        f"Merge branch '{branch_name}' into main",
        merged_tree,
                        [main_commit.id, feature_commit.id],
                    )
