# git2df Usage Patterns

This runbook demonstrates how to use the `git2df` library to extract commit data from a Git repository and load it into a Pandas DataFrame.

The primary function to use is `git2df.get_commits_df`.

## Backends

`git2df` uses different backends to extract data depending on the source of the repository.

*   **`GitCliBackend`**: This is the default backend and is used for local repositories. It uses the `git` command-line interface to extract data.
*   **`DulwichRemoteBackend`**: This backend is used for remote repositories. It uses the `dulwich` library to extract data directly from the remote repository without needing to clone it locally.

## Basic Usage

To get all commit data from the current repository:

```python
import git2df

# Get all commits from the current directory's git repository
df = git2df.get_commits_df()

print(df.head())
print(df.info())
```

### Analyze Remote Repositories (`remote_url`, `remote_branch`)

You can now analyze remote Git repositories directly without a local clone by providing a `remote_url`.

```python
import git2df

# Analyze a remote repository's 'main' branch
df_remote = git2df.get_commits_df(
    remote_url="https://github.com/pallets/flask",
    remote_branch="main",
    since="6 months ago"
)
print("Commits from remote Flask repository:")
print(df_remote.head())
```

*   `remote_url`: URL of the remote Git repository to analyze (e.g., `https://github.com/user/repo`). Mutually exclusive with `repo_path`.
*   `remote_branch`: Branch of the remote repository to analyze (default: `main`). Only applicable with `remote_url`.

## Filtering Commits

The `get_commits_df` function supports various parameters to filter the commits.

*   `repo_path`: The path to the git repository. Mutually exclusive with `remote_url`.
*   `remote_url`: URL of the remote Git repository to analyze (e.g., `https://github.com/user/repo`). Mutually exclusive with `repo_path`.
*   `remote_branch`: Branch of the remote repository to analyze (default: `main`). Only applicable with `remote_url`.

### Filter by Date (`since`, `until`)

To get commits within a specific date range:

```python
import git2df
from datetime import datetime

# Get commits since a specific date
df_since = git2df.get_commits_df(since=datetime(2023, 1, 1).isoformat())
print("Commits since Jan 1, 2023:")
print(df_since.head())

# Get commits until a specific date
df_until = git2df.get_commits_df(until=datetime(2023, 12, 31).isoformat())
print("\nCommits until Dec 31, 2023:")
print(df_until.head())

# Get commits between two dates
df_range = git2df.get_commits_df(since=datetime(2023, 6, 1).isoformat(), until=datetime(2023, 6, 30).isoformat())
print("\nCommits in June 2023:")
print(df_range.head())
```

### Filter by Author (`author`)

To get commits by a specific author:

```python
import git2df

# Get commits by a specific author (e.g., "John Doe" or "john.doe@example.com")
df_author = git2df.get_commits_df(author="Your Name")
print("Commits by 'Your Name':")
print(df_author.head())
```

### Filter by Commit Message (`grep`)

To get commits whose messages match a specific pattern:

```python
import git2df

# Get commits with "feature" in their message
df_grep = git2df.get_commits_df(grep="feature")
print("Commits with 'feature' in message:")
print(df_grep.head())
```

### Filter for Merged Commits Only (`merged_only`)

To get only commits that have been merged into the current branch:

```python
import git2df

# Get only merged commits
df_merged = git2df.get_commits_df(merged_only=True)
print("Merged commits only:")
print(df_merged.head())
```

### Filter by Included/Excluded Paths (`include_paths`, `exclude_paths`)

To get commits affecting specific files or directories, or to exclude them:

```python
import git2df

# Get commits affecting only files in the 'src/' directory
df_include = git2df.get_commits_df(include_paths=["src/"])
print("Commits affecting 'src/':")
print(df_include.head())

# Get commits excluding files in the 'docs/' directory
df_exclude = git2df.get_commits_df(exclude_paths=["docs/"])
print("\nCommits excluding 'docs/':")
print(df_exclude.head())

# Get commits affecting specific files
df_specific_files = git2df.get_commits_df(include_paths=["src/git2df/__init__.py", "src/git2df/backends.py"])
print("\nCommits affecting specific files:")
print(df_specific_files.head())
```

### Combined Filters

You can combine multiple filters:

```python
import git2df
from datetime import datetime

# Get commits by "John Doe" in 2023, affecting "src/" and with "bugfix" in message
df_combined = git2df.get_commits_df(
    since=datetime(2023, 1, 1).isoformat(),
    until=datetime(2023, 12, 31).isoformat(),
    author="John Doe",
    grep="bugfix",
    include_paths=["src/"]
)
print("Combined filter example:")
print(df_combined.head())
```

## DataFrame Structure

The `get_commits_df` function returns a Pandas DataFrame where **each row represents a single file change within a commit**. If a commit affects multiple files, there will be multiple rows for that commit, each detailing a specific file's change.

The DataFrame includes the following columns:

*   `commit_hash`: The full hash of the commit.
*   `parent_hash`: The hash of the parent commit.
*   `author_name`: The name of the commit author.
*   `author_email`: The email of the commit author.
*   `commit_date`: The timestamp of the commit.
*   `file_paths`: The path of the file that was changed in this specific row.
*   `change_type`: The type of change for this specific file (e.g., 'A' for added, 'M' for modified, 'D' for deleted).
*   `additions`: The number of lines added to this specific file.
*   `deletions`: The number of lines deleted from this specific file.
*   `commit_message`: The full commit message.

