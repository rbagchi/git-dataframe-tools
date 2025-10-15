## Current State of Test Suite and Code Quality

**Goal:** Ensure a robust and maintainable test suite with high code quality.

**Progress:**
- **Centralized CLI Argument Parsing:** Common CLI arguments have been centralized into `src/git_dataframe_tools/cli/common_args.py`, and both `git_df.py` and `scoreboard.py` have been refactored to use these common definitions, improving consistency and reducing boilerplate.
- **Encapsulated Backend Selection:** The backend selection logic in `git2df/__init__.py` has been refactored to consistently pass `repo_path` to `GitCliBackend` and streamline the `get_raw_log_output` calls, improving modularity and consistency.
- **Decomposed `_walk_commits`:** The `_walk_commits` method in `src/git2df/dulwich_backend.py` has been decomposed into smaller, more focused functions (`_collect_and_filter_commits` and `_process_single_commit`), improving readability, testability, and maintainability.
- **Dulwich Backend Output Alignment:** Aligned the output format of `_format_commit_line` in `src/git2df/dulwich_backend.py` with the expected input format of `_parse_commit_metadata_line` in `src/git2df/git_parser.py`.
- **Accurate Additions/Deletions Calculation:** Implemented accurate calculation of additions and deletions in `_extract_file_changes` within `src/git2df/dulwich_backend.py` by parsing `dulwich.patch.write_tree_diff` output, replacing the previous hardcoded values. Updated relevant tests accordingly.
- **Runbook and README Tests:** `tests/test_runbook.py` and `tests/test_readme.py` have been refactored to be data-driven, extracting code blocks directly from `RUNBOOK-git2df.md` and `README.md` respectively. This ensures documentation stays in sync with the application's behavior. The tests now run in the current Python environment, simplifying execution and improving speed.
- **Flaky Test Resolution:** The flaky test in `tests/test_git_integration.py` was resolved by correctly managing the current working directory within the `git_repo` fixture.
- **Pytest Output:** Restored default, less verbose `pytest` output by removing `log_cli` configuration.
- **Refined `dulwich_progress_callback`:** The `dulwich_progress_callback` function in `src/git2df/dulwich/repo_handler.py` has been refined to use regular expressions for more robust parsing of progress messages during remote fetches. This allows for more accurate updates to the `tqdm` progress bar by extracting total and current object counts from messages like "Receiving objects: X% (Y/Z), A bytes" and "Total X (delta Y), reused Z (delta W)". This replaces the previous keyword-based matching, improving the reliability and accuracy of progress reporting.
- **Deprecated Dulwich API:** Updated `_create_dulwich_commit` in `tests/conftest.py` to use modern `dulwich` APIs, removing deprecation warnings.
- **Golden Files for Parser Tests:** Implemented a golden files approach for `tests/test_git2df_parser.py`, moving test data into external `.log` and `.json` files for improved readability and maintainability.
- **Refined CLI Testing Strategy:** Refactored `tests/test_git_df_cli.py` and `tests/test_scoreboard.py` to use a black-box testing approach. These tests now run CLI commands against real git repositories created by the `git_repo` fixture, removing brittle mocking and providing more robust validation.
- **Code Duplication Reduction:** Consolidated `sample_commits` data and the `extract_code_blocks` helper function into `tests/conftest.py`, improving code reuse and maintainability. The `tests` directory was made a Python package to facilitate cleaner imports.
- **`tqdm` Integration:** Added `tqdm` progress bars for Dulwich remote fetches and parsing, with determinate progress for parsing.
- **TTY Detection:** Implemented logic to disable `tqdm` progress bars when output is not to a TTY (checking `sys.stdout.isatty()`).
- **Color Output:** Disabled color output when not writing to a TTY.
- **Date Parsing:** Improved date parsing in `DulwichRemoteBackend` using `parsedatetime`.
- **Refactored `git_parser.py` for Robustness:**
    - Introduced `FileChange` and `GitLogEntry` dataclasses for structured data representation.
    - Modularized parsing logic with helper functions (`_parse_commit_metadata_line`, `_parse_file_stat_line`, `_process_raw_commit_block`).
    - Refactored `_parse_git_data_internal` to use these new helper functions and return `List[GitLogEntry]`.
- **Updated `dataframe_builder.py`:**
    - Modified `build_commits_df` to accept `List[GitLogEntry]`.
- **Migrated CLI to `Typer`:**
    - Refactored `git_df.py` and `scoreboard.py` from `argparse` to `Typer`.
    - Updated `pyproject.toml` to reflect the new `Typer` entry points.
- **Refactored `dulwich_backend.py`:**
    - Decomposed `_walk_commits` into smaller, more focused helper methods (`_filter_commits_by_date`, `_filter_commits_by_author_and_grep`, `_format_commit_line`).
- **Modularized `DulwichRemoteBackend`:** Extracted file change analysis logic into a new class, `DulwichDiffParser`, in `src/git2df/dulwich_diff_parser.py`. This significantly reduced the complexity of `DulwichRemoteBackend`.
- **Updated Tests:**
    - Split `tests/test_git2df_public_api.py` into multiple, more focused test files.
    - Updated various tests to align with `Typer` CLI structure and new data types.
    - Resolved all `ruff` linting and `mypy` type-checking issues.
- **Resolved `TypeError: 'NoneType' object is not subscriptable`**: Fixed `_build_git_log_arguments` to return `cmd`.
- **Resolved `StopIteration` in `test_git2df_backends.py`**: Corrected `mock_subprocess_run.side_effect` setup in backend tests.
- **Resolved `IndentationError` in `tests/test_git2df_backends.backends.py`**: Fixed indentation issues in backend tests.
- **Resolved `NameError` for `Optional` and `List`**: Added missing imports in `tests/test_git_stats_pandas.py` and `tests/test_scoreboard.py`.
- **Resolved `NameError` for `re`**: Moved `import re` to the top of `tests/test_scoreboard.py`.
- **Resolved `pytest` failures in `tests/test_scoreboard_df_path.py`**: The `exit_code == 2` issue was resolved by simplifying the `df_path` argument definition in `src/git_dataframe_tools/cli/scoreboard.py`.
- **Cyclomatic Complexity Analysis (Radon) - All functions now 'B' grade or better:**
    *   `tests/test_git_df.py`: All functions are now 'A' grade.
    *   `tests/test_git2df_integration.py`: All functions are now 'B' grade or better.
    *   `src/git2df/backends.py`: All functions are now 'B' grade or better.
    *   `src/git2df/dulwich/diff_parser.py`: All functions are now 'B' grade or better.
    *   `src/git_dataframe_tools/git_stats_pandas.py`: All functions are now 'B' grade or better.
    *   `src/git_dataframe_tools/cli/scoreboard.py`: All functions are now 'B' grade or better.
    *   `src/git_dataframe_tools/cli/_data_loader.py`: All functions are now 'B' grade or better.
    *   `src/git_dataframe_tools/cli/_display_utils.py`: All functions are now 'B' grade or better.
    *   `tests/test_readme.py`: All functions are now 'A' grade.
    *   `tests/test_git_df_cli.py`: All functions are now 'A' grade.
    *   `tests/test_scoreboard.py`: All functions are now 'A' grade.
    *   `tests/test_git2df_backends.py`: Refactored to use helper functions, significantly reducing complexity of individual test functions to 'A' and 'B' grades.
- **Decomposed `git_parser.py` into a multi-file module:** The `git_parser.py` file has been broken down into a multi-file module, improving modularity, readability, and testability by separating distinct parsing concerns.
- **Enhanced `git_parser.py` robustness:** The parsing logic in `git_parser.py` has been enhanced, making it more resilient to changes in `git log` output format.
- **Used a table formatting library:** Manual string formatting for tables in `_display_utils.py` has been replaced with a library like `tabulate`, improving output presentation and simplifying display logic.
- **Decoupled `GitAnalysisConfig` from `GitPython`:** The `_set_current_git_user` and `_check_git_repo` methods in `config_models.py` no longer directly use `GitPython`, abstracting Git repository interactions and improving testability and flexibility.
- **Integrated `loguru` for logging:** `loguru` has been integrated for advanced logging features and easier configuration.
- **Accurate `change_type` determination:** The `change_type` logic has been improved to accurately reflect all Git change types (e.g., "R" for rename, "C" for copy) by correctly parsing `git show --name-status` output.
- **Refactored `GitCliBackend` and Fixed Static Analysis Errors:** Refactored `GitCliBackend` to implement the `GitBackend` interface, as part of the backend standardization plan. Implemented `get_log_entries` to return structured data, added `_get_default_branch` to fetch the default branch name, refactored `_build_git_log_arguments` to reduce cyclomatic complexity, and removed a duplicated `get_raw_log_output` method. Also addressed several static analysis issues, including `ruff` errors, `radon` cyclomatic complexity, and fixed broken unit tests.
- **Refactored `DulwichRemoteBackend` to Implement `GitBackend`**: Refactored `DulwichRemoteBackend` to implement the `GitBackend` interface. This included adding the `get_log_entries` method, inheriting from `GitBackend`, and deprecating the `get_raw_log_output` method.
- **Updated `get_commits_df` to Use `get_log_entries`**: Refactored `get_commits_df` in `src/git2df/__init__.py` to call `backend.get_log_entries()` directly, removing the separate parsing step and simplifying the data flow. Updated and fixed related unit tests.
- **Implemented File Change Extraction and Filtering for `Pygit2Backend` (Step 5.4):**
    - Verified `patch.delta.new_file.path` for various change types (add, modify, delete, rename, copy).
    - Verified path filtering (`include_paths`/`exclude_paths`) with various scenarios.
    - Verified additions/deletions/change type for basic file modifications.
    - Verified additions/deletions/change type for renames and copies.
    - Verified special handling for initial commits.
- **Resolved `AttributeError: module 'parsedatetime' has no attribute 'CONTEXT_DATE'`**: Fixed `src/git2df/date_utils.py` to correctly use `pdt.pdtContext.ACU_DATE` and ensured proper date filtering by passing explicit start/end of day `datetime` objects as `sourceTime` to `cal.parseDT`.
