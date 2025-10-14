import subprocess


def test_initial_commit_diff_tree(git_repo):
    """Tests that git diff-tree against the initial commit hash returns nothing."""
    initial_commit_hash = subprocess.check_output(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=git_repo).decode().strip()
    
    # This is expected to fail for the initial commit
    output = subprocess.check_output(["git", "diff-tree", "-r", initial_commit_hash], cwd=git_repo).decode().strip()
    assert output == ""

    # This should work
    output = subprocess.check_output(["git", "diff-tree", "-r", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", initial_commit_hash], cwd=git_repo).decode().strip()
    assert "initial_file.txt" in output

def test_diff_tree_output_format(git_repo):
    """Tests the output format of git diff-tree --numstat and --name-status."""
    with open("new_file.txt", "w") as f:
        f.write("new content")
    subprocess.check_call(["git", "add", "new_file.txt"], cwd=git_repo)
    subprocess.check_call(["git", "commit", "-m", "new commit"], cwd=git_repo)

    numstat_output = subprocess.check_output(["git", "diff-tree", "-r", "--numstat", "HEAD"], cwd=git_repo).decode().strip()
    assert "1\t0\tnew_file.txt" in numstat_output

    name_status_output = subprocess.check_output(["git", "diff-tree", "-r", "--name-status", "HEAD"], cwd=git_repo).decode().strip()
    assert "A\tnew_file.txt" in name_status_output

def test_initial_commit_parent_hash(git_repo):
    """Tests that the initial commit has an empty parent hash."""
    initial_commit_hash = subprocess.check_output(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=git_repo).decode().strip()
    parent_hash = subprocess.check_output(["git", "show", "-s", "--pretty=format:%P", initial_commit_hash], cwd=git_repo).decode().strip()
    assert parent_hash == ""
