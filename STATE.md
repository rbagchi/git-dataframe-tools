## Current Work: Refactoring `git-scoreboard` into a Library and CLIs

I am currently refactoring the `git-scoreboard` project into a modular `git2df` library and two command-line applications, following the plan outlined in `REFACTORING_PLAN.md`.

**Current Progress (Phase 1: Establish `git2df` Library - CLI-based):**

We are working on the `refactor/git2df-library` branch.

**Completed Steps:**

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

**Next Steps:**

We are about to proceed with **Step 7: Add Basic Filtering to `GitCliBackend`** as outlined in `REFACTORING_PLAN.md`.
