# DULWICH-PLAN.MD: On-the-Fly Remote Git Analysis with Dulwich

This plan outlines the steps to enable `git-df` and `git-scoreboard` to analyze public Git repositories on-the-fly using `dulwich`, without requiring a persistent local clone. The primary use case is to fetch the `3.14` branch of `https://github.com/python/cpython` for the past year, extracting all commit details as if it were a local clone.

## Goal

Implement a new backend for `git2df` that utilizes `dulwich` to fetch Git history and diffs directly from a remote HTTP(S) URL, allowing `git-df` and `git-scoreboard` to analyze remote repositories without local cloning.

## Use Case: CPython 3.14 Branch for the Last Year

*   **Repository URL:** `https://github.com/python/cpython`
*   **Branch:** `3.14`
*   **Timeframe:** Last year from the current date.
*   **Desired Output:** A Pandas DataFrame with the same detailed commit and file change information as a local `git clone` would provide.

## Achievable Steps

### Phase 1: Dulwich Research and Basic Fetch

1.  **Understand Dulwich Remote Fetch:**
    *   **Action:** Research `dulwich`'s capabilities for fetching from remote HTTP(S) repositories. Identify the core `dulwich` classes and functions for this (e.g., `dulwich.client.HTTPClient`, `dulwich.repo.Repo.get_object`, `dulwich.repo.Repo.do_fetch`).
    *   **Expected Outcome:** Clear understanding of how to initiate a remote fetch and access fetched objects.
2.  **Basic Remote Fetch Proof of Concept (PoC):**
    *   **Action:** Write a small Python script using `dulwich` to connect to `https://github.com/python/cpython`, fetch the `3.14` branch's head commit, and print its hash and message. Do this without creating any persistent local files.
    *   **Expected Outcome:** A working script demonstrating basic remote fetching.

### Phase 2: Reconstructing Commit History

1.  **Iterate Commits from Remote:**
    *   **Action:** Extend the PoC script to iterate through the commit history of the `3.14` branch, starting from the fetched head commit, and print the hash, author, date, and message for each commit.
    *   **Challenge:** Implement logic to stop iterating at a specific date (e.g., "last year"). `dulwich` might require iterating and filtering locally, or there might be remote filtering options.
    *   **Expected Outcome:** A script that can traverse the commit history of the remote branch for the specified timeframe.
2.  **Extract Commit Metadata:**
    *   **Action:** For each commit, extract all necessary metadata: `commit_hash`, `parent_hash`, `author_name`, `author_email`, `commit_date`, `commit_message`.
    *   **Expected Outcome:** A list of dictionaries, each representing a commit with its metadata.

### Phase 3: Extracting File Changes (Diffs)

1.  **Understand Dulwich Diffing:**
    *   **Action:** Research how `dulwich` handles diffs between commits. Identify functions to compare two tree objects (parent commit's tree vs. current commit's tree) to get file changes (additions, deletions, change type, file paths).
    *   **Expected Outcome:** Understanding of `dulwich`'s diffing API.
2.  **Implement Diff Extraction:**
    *   **Action:** Integrate diff extraction into the commit iteration. For each commit, compare its tree with its parent's tree to get the list of changed files, along with `additions`, `deletions`, and `change_type`.
    *   **Challenge:** Handling initial commits (no parent) and merge commits (multiple parents).
    *   **Expected Outcome:** A script that extracts detailed file change information for each commit.

### Phase 4: Integrating into `git2df`

1.  **Create `DulwichRemoteBackend`:**
    *   **Action:** Create a new class `DulwichRemoteBackend` in `src/git2df/backends.py` (or a new file like `src/git2df/remote_backends.py`). This class will encapsulate the `dulwich` logic developed in Phases 1-3.
    *   **Interface:** Ensure it conforms to an abstract backend interface (if one exists or is created) that `git2df.get_commits_df` can use.
2.  **Modify `git2df.get_commits_df`:**
    *   **Action:** Add `remote_url: Optional[str]` to its signature.
    *   **Logic:** If `remote_url` is provided, instantiate and use the `DulwichRemoteBackend`. Otherwise, use the existing `GitPython` backend.
    *   **Parameter Mapping:** Map `get_commits_df` parameters (like `since`, `until`, `author`, `grep`, `include_paths`, `exclude_paths`) to `dulwich`'s filtering capabilities or implement post-fetch filtering.
3.  **Temporary Object Store Management:**
    *   **Action:** Ensure any temporary disk-based object stores created by `dulwich` are properly cleaned up after `get_commits_df` completes. If `dulwich` can operate purely in-memory for this use case, this step might be simplified.

### Phase 5: CLI Integration and Testing

1.  **Modify `git-df` CLI:**
    *   **Action:** Add `--remote-url <url>` option to `git-df`.
    *   **Logic:** If `--remote-url` is used, pass it to `git2df.get_commits_df`. Ensure mutual exclusivity with `repo_path`.
2.  **Modify `git-scoreboard` CLI:**
    *   **Action:** Add `--remote-url <url>` option to `git-scoreboard`.
    *   **Logic:** If `--remote-url` is used, internally call `git2df.get_commits_df` with the `remote_url` and then proceed with analysis. Ensure mutual exclusivity with `repo_path` and `--df-path`.
3.  **Update Documentation:**
    *   **Action:** Update `README.md` and `RUNBOOK-git2df.md` to reflect the new `--remote-url` option and its usage.
4.  **Add Comprehensive Tests:**
    *   **Action:** Write unit tests for the `DulwichRemoteBackend`.
    *   **Action:** Write integration tests for `git-df` and `git-scoreboard` using `--remote-url` against `https://github.com/python/cpython` (or a smaller, dedicated test repository) for the specified branch and timeframe. Mock network interactions where necessary.
