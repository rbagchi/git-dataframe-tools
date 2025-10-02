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

*   **Phase 3: Refactor `git-scoreboard` CLI**
    *   Modified `src/git_scoreboard/config_models.py` to replace the `get_git_log_data` method. It now imports `get_commits_df` from `git2df`, returns a `pd.DataFrame`, and calls `get_commits_df` with appropriate arguments. All direct `subprocess.run` calls for `git log` have been removed from this method.
    *   Updated `tests/test_git_interaction.py` to mock `git2df.get_commits_df` instead of `subprocess.run`, and adjusted assertions to expect a Pandas DataFrame. All `test_git_interaction.py` tests are passing.
    *   Updated `src/git_scoreboard/git_stats_pandas.py` and `src/git_scoreboard/git_stats.py` to accept a DataFrame, and their tests (`tests/test_git_stats_pandas.py` and `tests/test_compatibility.py`) are passing.
    *   Updated `src/git_scoreboard/scoreboard.py` to remove the local `tqdm` import and `_parse_period_string` import.
    *   Updated `tests/test_git_integration.py` to correctly assert against the DataFrame returned by `git2df.get_commits_df` and are now passing.

**Next Steps:**

Proceed with **Phase 2: Develop `git-extract-commits` CLI** as outlined in `REFACTORING_PLAN.md`.
