## Current Work: Refactoring `git-scoreboard` into a Library and CLIs

I am currently refactoring the `git-scoreboard` project into a modular `git2df` library and two command-line applications, following the plan outlined in `REFACTORING_PLAN.md`.

**Completed Phases:**

*   **Phase 1: Establish `git2df` Library (CLI-based)**
    *   **Step 1: Create the `git2df` Package Structure**
        *   Created `src/git2df/` and `src/git2df/__init__.py`.
    *   **Step 2: Extract `_run_git_command` Utility**
        *   Moved core `git` command execution logic to `src/git2df/git_cli_utils.py`.
        *   Implemented and passed unit tests for `_run_git_command`.
    *   **Step 3: Copy Raw `git log` Output Parsing Logic**
        *   Copied `_parse_git_data_internal` to `src/git2df/git_parser.py`.
        *   Implemented and passed unit tests for `_parse_git_data_internal`.
    *   **Step 4: Implement Basic `GitCliBackend` Class**
        *   Created `src/git2df/backends.py` with `GitCliBackend` and its `get_raw_log_output` method.
        *   Implemented and passed unit tests for `GitCliBackend`.
    *   **Step 5: Convert Parsed Data to Basic Pandas DataFrame**
        *   Created `src/git2df/dataframe_builder.py` with `build_commits_df`.
        *   Implemented and passed unit tests for `build_commits_df`.
    *   **Step 6: Create Public `get_commits_df` Function (No Filters)**
        *   Defined `get_commits_df` in `src/git2df/__init__.py` as the main entry point.
        *   Implemented and passed unit tests for `get_commits_df`.
    *   **Integration Tests for `get_commits_df`**
        *   Implemented and passed integration tests using a dummy Git repository.
        *   Enhanced integration tests to correlate `git2df` output with direct `git log` output.
        *   Added an integration test using a cloned public repository (`https://github.com/octocat/Spoon-Knife.git`) which also passed.
    *   **Step 7: Add Basic Filtering to `GitCliBackend`**
        *   Modified `get_raw_log_output` in `src/git2df/backends.py` to accept `since`, `until`, `author`, and `grep` arguments.
        *   Modified `get_commits_df` in `src/git2df/__init__.py` to pass these filtering arguments to `GitCliBackend`.
        *   Implemented and passed unit tests for the new filtering functionality.
    *   **Extended `git2df` with `merged_only`, `include_paths`, `exclude_paths`:**
        *   Modified `src/git2df/backends.py` to add `merged_only`, `include_paths`, and `exclude_paths` parameters to `GitCliBackend.get_raw_log_output` and incorporated them into the `git log` command.
        *   Modified `src/git2df/__init__.py` to add `merged_only`, `include_paths`, and `exclude_paths` parameters to `get_commits_df` and passed them to `GitCliBackend.get_raw_log_output`.
        *   Updated `tests/test_git2df_backends.py` and `tests/test_git2df_public_api.py` with new test cases to cover the new filtering parameters. All `git2df` tests are passing.
    *   **Refactored `git2df` to output commit-centric DataFrame:**
        *   Modified `src/git2df/git_parser.py` to parse individual commit details and file changes.
        *   Modified `src/git2df/dataframe_builder.py` to construct a DataFrame with one row per file change per commit, including `commit_hash`, `parent_hash`, `author_name`, `author_email`, `commit_date`, `file_paths`, `change_type`, `additions`, `deletions`, and `commit_message`.
        *   Updated `src/git2df/__init__.py` to use the new parsing and DataFrame building logic.
        *   Updated `tests/test_git2df_parser.py`, `tests/test_git2df_dataframe_builder.py`, `tests/test_git2df_public_api.py`, `tests/test_git_extract_commits.py`, `tests/test_git_integration.py`, and `tests/test_git_interaction.py` to assert against the new commit-centric DataFrame structure. All these tests are now passing.
*   **Phase 3: Refactor `git-scoreboard` CLI**
    *   Modified `src/git_scoreboard/config_models.py` to replace the `get_git_log_data` method. It now imports `get_commits_df` from `git2df`, returns a `pd.DataFrame`, and calls `get_commits_df` with appropriate arguments. All direct `subprocess.run` calls for `git log` have been removed from this method.
    *   Updated `tests/test_git_interaction.py` to mock `git2df.get_commits_df` instead of `subprocess.run`, and adjusted assertions to expect a Pandas DataFrame. All `test_git_interaction.py` tests are passing.
    *   Updated `src/git_scoreboard/git_stats_pandas.py` and `src/git_scoreboard/git_stats.py` to accept a DataFrame, and their tests (`tests/test_git_stats_pandas.py` and `tests/test_compatibility.py`) are passing.
    *   Updated `src/git_scoreboard/scoreboard.py` to remove the local `tqdm` import and `_parse_period_string` import.
    *   Updated `tests/test_git_integration.py` to correctly assert against the DataFrame returned by `git2df.get_commits_df` and are now passing.
    *   **Added `--df-path` argument to `src/git_scoreboard/scoreboard.py`:** This allows `git-scoreboard` to operate on a pre-extracted DataFrame from a Parquet file, enhancing modularity and flexibility.
    *   **Implemented major version checking for `--df-path` in `src/git_scoreboard/scoreboard.py`:** Ensures compatibility of loaded DataFrames with the expected data schema, with an option (`--force-version-mismatch`) to override the check.

*   **Phase 2: Develop `git-df` CLI**
    *   **Step 1: Implement `git-df` CLI**
        *   Implemented `src/git_scoreboard/git_df.py` (formerly `git-extract-commits`) to extract filtered Git commit data and save it to a Parquet file.
        *   Made `git-df` tests portable by replacing hardcoded `uv` commands with `sys.executable`.
        *   Renamed `src/git_scoreboard/git_extract_commits.py` to `src/git_scoreboard/git_df.py` and `tests/test_git_extract_commits.py` to `tests/test_git_df.py`.
        *   Updated internal references and help messages in `git_df.py`.
        *   Added metadata (including a `data_version`) to the Parquet output of `git-df`.
        *   Updated `tests/test_git_df.py` to verify the presence and content of the Parquet metadata. All `git-df` tests are passing.

**Next Steps:**

Proceed with **Phase 3: Refactor `git-scoreboard` CLI** as outlined in `REFACTORING_PLAN.md`.
