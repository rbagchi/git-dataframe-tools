# Git Backend Standardization Plan

## Goal
To standardize all Git backends within `git-dataframe-tools` to directly return structured `List[GitLogEntry]` objects, eliminating the need for external raw string parsing and simplifying the overall data flow. This will improve maintainability, extensibility, and type safety.

## Current State
*   `GitCliBackend` provides `get_raw_log_output` (returns `str`) which is then parsed by `parse_git_log`.
*   `DulwichRemoteBackend` provides both `get_raw_log_output` (returns `str`) and `get_log_entries` (returns `List[GitLogEntry]`), but `get_commits_df` currently uses `get_raw_log_output` for all backends.
*   `get_commits_df` in `src/git2df/__init__.py` contains logic to call `get_raw_log_output` and then `parse_git_log`.
*   The project uses `GitLogEntry` and `FileChange` dataclasses as its canonical data structures for commit information.

## Proposed Architecture
All Git backends will implement a common interface (`GitBackend` Protocol/ABC) that exposes a `get_log_entries` method. This method will be responsible for fetching Git data and transforming it into `List[GitLogEntry]` objects. The `get_commits_df` function will then simply call `backend.get_log_entries()` and pass the result directly to `build_commits_df`.

## Detailed Steps

### Step 1: Define a Formal `GitBackend` Interface (Protocol/ABC)
*   **Description:** Create an abstract base class (using `abc.ABC`) or a `typing.Protocol` that defines the `get_log_entries` method. This method will serve as the contract for all Git backends.
*   **Rationale:** Ensures all backends adhere to a consistent API, improving type safety and making future backend implementations straightforward.
*   **Location:** `src/git2df/backends.py` (or a new `src/git2df/backend_interface.py` if preferred for separation).
*   **Level of Effort:** Low
*   **Action:**
    *   Create `GitBackend` abstract class with `get_log_entries` as an abstract method.
    *   The method signature should include all common filtering arguments: `log_args`, `since`, `until`, `author`, `grep`, `merged_only`, `include_paths`, `exclude_paths`.
    *   The return type must be `List[GitLogEntry]`.

### Step 2: Refactor `GitCliBackend` to Implement `GitBackend`
*   **Description:** Modify `GitCliBackend` to inherit from the new `GitBackend` interface and implement its `get_log_entries` method.
*   **Rationale:** Aligns `GitCliBackend` with the new standardized interface, centralizing the parsing logic within the backend itself.
*   **Location:** `src/git2df/backends.py`
*   **Level of Effort:** Medium
*   **Action:**
    *   Make `GitCliBackend` inherit from `GitBackend`.
    *   Implement `get_log_entries` in `GitCliBackend`.
    *   Inside `get_log_entries`:
        *   Utilize existing `_build_git_log_arguments` and `_run_git_command` to get raw `git log` output.
        *   Call `parse_git_log` (from `git2df.git_parser`) internally to convert the raw string into `List[GitLogEntry]`.
        *   Return the `List[GitLogEntry]`.
    *   **Deprecate `get_raw_log_output`:** Add a clear docstring to `GitCliBackend.get_raw_log_output` indicating its deprecation.

### Step 3: Refactor `DulwichRemoteBackend` to Implement `GitBackend`
*   **Description:** Modify `DulwichRemoteBackend` to inherit from `GitBackend` and ensure its existing `get_log_entries` method fully conforms to the interface.
*   **Rationale:** Ensures consistency for the Dulwich backend and prepares for its direct usage.
*   **Location:** `src/git2df/dulwich/backend.py`
*   **Level of Effort:** Low
*   **Action:**
    *   Make `DulwichRemoteBackend` inherit from `GitBackend`.
    *   Verify that its existing `get_log_entries` method matches the signature and return type of the `GitBackend` interface.
    *   **Deprecate `get_raw_log_output`:** Add a clear docstring to `DulwichRemoteBackend.get_raw_log_output` indicating its deprecation.

### Step 4: Update `get_commits_df` in `src/git2df/__init__.py`
*   **Description:** Simplify `get_commits_df` to always call `backend.get_log_entries()` directly, removing conditional logic and external parsing.
*   **Rationale:** Streamlines the data retrieval process, making `get_commits_df` cleaner and more focused on orchestrating backend calls and DataFrame building.
*   **Location:** `src/git2df/__init__.py`
*   **Level of Effort:** Low
*   **Action:**
    *   Remove the `isinstance` checks for backend types.
    *   Remove the direct call to `parse_git_log`.
    *   Modify the code to simply call `parsed_entries = backend.get_log_entries(...)` for all backends.

### Step 5: Implement `Pygit2Backend`

*   **Description:** Create a new backend class, `Pygit2Backend`, that implements the `GitBackend` interface using the `pygit2` library.
*   **Rationale:** Provides a more performant and native Git database access option.
*   **Location:** `src/git2df/pygit2_backend.py`

#### Step 5.1: Add `pygit2` Dependency and Create `Pygit2Backend` Skeleton
*   **Description:** Add `pygit2` to the project's dependencies in `pyproject.toml` and install it. Then, create the new file `src/git2df/pygit2_backend.py` with a basic `Pygit2Backend` class that inherits from `GitBackend` and has a placeholder for the `get_log_entries` method.
*   **Level of Effort:** Low
*   **Status:** COMPLETE

#### Step 5.2: Implement Commit Walking and Metadata Extraction
*   **Description:** Implement the initial version of `get_log_entries` to walk the commit history using `pygit2`. For each commit, extract the essential metadata (hash, author, date, message) and create `GitLogEntry` objects, leaving the `file_changes` list empty for now.
*   **Level of Effort:** Medium
*   **Status:** COMPLETE

#### Step 5.3: Implement Commit Filtering
*   **5.3.1: Filter by Date (`since`/`until`):** Add logic to filter commits based on their commit time. (Low)
*   **Status:** COMPLETE
*   **5.3.2: Filter by Author:** Add logic to filter commits by the author's name or email. (Low)
*   **Status:** COMPLETE
*   **5.3.3: Filter by Message (`grep`):** Add logic to filter commits by searching for a pattern in the commit message. (Low)
*   **Status:** COMPLETE
*   **5.3.4: Implement `merged_only` filter:** Add logic to filter commits that are part of a merge. (Low)
*   **Status:** COMPLETE

#### Step 5.4: Implement File Change Extraction and Filtering
*   **5.4.1: Extract Changed File Paths:** For each commit, get the list of file paths that were modified. (Low)
*   **Status:** COMPLETE
*   **5.4.2: Filter by Path (`include_paths`/`exclude_paths`):** Filter the commits based on the file paths from the previous step. (Low)
*   **Status:** COMPLETE
*   **5.4.3: Extract Additions, Deletions, and Change Type:** For each file, parse the diff to get the number of added/deleted lines and the type of change (e.g., 'A', 'M', 'D'). (Medium)
*   **Status:** COMPLETE

#### Step 5.5: Utilize `log_args` parameter
*   **Status:** COMPLETE

### Step 6: Refine `_get_git_backend` Factory
*   **Description:** Update the `_get_git_backend` factory function to correctly instantiate the desired backend based on configuration (e.g., local vs. remote, preferred local backend).
*   **Rationale:** Ensures the correct backend is chosen dynamically.
*   **Location:** `src/git2df/__init__.py`
*   **Level of Effort:** Low
*   **Action:**
    *   Modify the logic to return instances of the new `GitBackend` implementations.
    *   Consider adding a configuration option to select the preferred local backend (e.g., `GitCliBackend` vs. `Pygit2Backend`).
*   **Status:** COMPLETE

### Step 7: Comprehensive Testing
*   **Description:** Develop and update unit and integration tests to ensure all backends correctly implement the `GitBackend` interface and produce accurate `List[GitLogEntry]` objects.
*   **Rationale:** Guarantees the correctness and reliability of all backend implementations.
*   **Location:** `tests/` directory
*   **Level of Effort:** High (requires creating new tests for the new backend, updating existing ones)
*   **Action:**
    *   Create `tests/test_pygit2_backend.py` (or similar) with tests covering all aspects of `get_log_entries` (metadata, file changes, filtering).
    *   Review and update existing tests for `GitCliBackend` and `DulwichRemoteBackend` to ensure they now test the `get_log_entries` method.
*   **Status:** IN PROGRESS
    *   Initial unit/integration tests for `Pygit2Backend` are passing, including verification of `patch.delta.new_file.path` for various change types, path filtering, additions/deletions/change type for basic modifications, renames/copies, and special handling for initial commits.

### Step 7.5: Cross-Backend Result Verification
*   **Description:** Implement integration tests that compare the `List[GitLogEntry]` output of PyGit2, CLI, and Dulwich backends for a set of common test repositories and filter configurations.
*   **Rationale:** This step is critical for building confidence in the correctness and consistency of all backend implementations, ensuring they produce identical results for the same input.
*   **Location:** `tests/` directory
*   **Level of Effort:** High
*   **Status:** IN PROGRESS

#### Step 7.5.1: Add comprehensive test cases for `Pygit2Backend` filters
*   **Description:** Add dedicated test cases in `tests/test_pygit2_backend.py` to explicitly verify the functionality of `author`, `grep`, `until`, and `exclude_paths` filters.
*   **Level of Effort:** Low
*   **Status:** COMPLETE
    *   **7.5.1.1: Add `author` filter test for `Pygit2Backend`**
        *   **Status:** COMPLETE
    *   **7.5.1.2: Add `grep` filter test for `Pygit2Backend`**
        *   **Status:** COMPLETE
    *   **7.5.1.3: Add `until` filter test for `Pygit2Backend`**
        *   **Status:** COMPLETE
    *   **7.5.1.4: Add `exclude_paths` filter test for `Pygit2Backend`**
        *   **Status:** COMPLETE
        *   **Status:** COMPLETE

#### Step 7.5.2: Expand `test_backend_consistency.py` with more filter combinations
*   **Description:** Add more `@pytest.mark.parametrize` entries to `tests/test_backend_consistency.py` to cover a wider range of filter combinations for all backends.
*   **Level of Effort:** Medium
*   **Status:** COMPLETE
    *   **7.5.2.1: Add `since` and `until` combination to consistency tests**
        *   **Status:** COMPLETE
    *   **7.5.2.2: Add `author` and `grep` combination to consistency tests**
        *   **Status:** COMPLETE
    *   **7.5.2.3: Add `include_paths` and `exclude_paths` combination to consistency tests**
        *   **Status:** COMPLETE
    *   **7.5.2.4: Add a comprehensive filter combination to consistency tests**
        *   **Status:** COMPLETE

#### Step 7.5.3: Add edge case tests to `test_backend_consistency.py`
*   **Description:** Create specific test cases in `tests/test_backend_consistency.py` for scenarios like empty repositories, commits with no parents, commits with unusual characters in messages/authors, and very large number of commits/files.
*   **Level of Effort:** Medium
*   **Status:** IN PROGRESS
    *   **7.5.3.1: Add empty repository test to consistency tests**
        *   **Status:** COMPLETE
    *   **7.5.3.2: Add commit with no parents test to consistency tests**
        *   **Status:** COMPLETE
    *   **7.5.3.3: Add unusual characters test to consistency tests**

#### Step 7.5.4: Add tests for diverse repository structures
*   **Description:** Create new fixtures or modify existing ones to generate more complex repository histories (e.g., repositories with many branches, merges, submodules, large binary files, empty commits) and add corresponding tests in `tests/test_backend_consistency.py`.
*   **Level of Effort:** High
*   **Status:** IN PROGRESS
    *   **7.5.4.1: Add multiple branches test to consistency tests**
    *   **7.5.4.2: Add merge commits test to consistency tests**
    *   **7.5.4.3: Add large binary files test to consistency tests**

#### Step 7.5.5: Verify `merged_only` behavior across backends
*   **Description:** Once the `merged_only` filter is implemented in `Pygit2Backend`, add test cases to `tests/test_backend_consistency.py` to verify its consistent behavior across all backends.
*   **Level of Effort:** Low
*   **Status:** IN PROGRESS
    *   **7.5.5.1: Add `merged_only` test for `Pygit2Backend`**
    *   **7.5.5.2: Add `merged_only` consistency test**

*   **Action:**
    *   Created `tests/test_backend_consistency.py` for cross-backend verification.
    *   Implemented detailed comparison of `GitLogEntry` objects, including sorting and timestamp tolerance.
    *   Resolved `NameError`, `AttributeError`, and `TypeError` issues in test setup.
    *   Successfully tested `GitCliBackend` and `Pygit2Backend` for basic commit data and various filter combinations.
    *   `DulwichRemoteBackend` is now being tested with a local bare remote repository.

### Step 8: Cleanup and Removal of Deprecated Code
*   **Description:** Remove the deprecated `get_raw_log_output` methods and the `parse_git_log` function once all code paths are confirmed to use `get_log_entries`.
*   **Rationale:** Reduces technical debt, removes unused code, and simplifies the codebase.
*   **Location:** `src/git2df/backends.py`, `src/git2df/dulwich/backend.py`, `src/git2df/git_parser/__init__.py`
*   **Level of Effort:** Low
*   **Action:**
    *   Delete `get_raw_log_output` from all backend classes.
    *   Delete the `parse_git_log` function.
*   **Status:** TO DO

#### Step 8.1: Remove `get_raw_log_output` from `GitCliBackend`
*   **Description:** Delete the `get_raw_log_output` method from `src/git2df/backends.py`.
*   **Level of Effort:** Low
*   **Status:** TO DO

#### Step 8.2: Remove `get_raw_log_output` from `DulwichRemoteBackend`
*   **Description:** Delete the `get_raw_log_output` method from `src/git2df/dulwich/backend.py`.
*   **Level of Effort:** Low
*   **Status:** TO DO

#### Step 8.3: Remove `parse_git_log` function
*   **Description:** Delete the `parse_git_log` function from `src/git2df/git_parser/__init__.py`.
*   **Level of Effort:** Low
*   **Status:** TO DO

This plan provides a clear roadmap for standardizing the Git backend architecture, leading to a more robust and maintainable system.
