**Current Work:** Improving Code Coverage and Quality

**Progress:**
*   **Added Code Quality Tools:**
    *   `mypy` for static type checking. All type errors resolved.
    *   `pytest-cov` for test coverage analysis.
    *   `radon` for cyclomatic complexity analysis.
*   **Refactored `src/git_dataframe_tools/cli/git_df.py`:**
    *   Extracted core logic into `run_git_df_cli` for testability.
    *   Wrote unit tests for `run_git_df_cli`, increasing coverage for `git_df.py` to 69%.
    *   Fixed `SystemExit` handling in `git_df_cli` tests.

*   **Completed:** Debugging `tests/test_scoreboard.py`
    *   Resolved all failing tests.
    *   Addressed `IndentationError` and `datetime.now()` mocking issues.
    *   Refactored `scoreboard.main()` to return status codes instead of calling `sys.exit()`.
    *   Resolved mypy errors in `tests/test_git2df_integration.py` and `tests/test_git_stats_pandas.py`.
    *   Refactored `src/git_dataframe_tools/cli/scoreboard.py` into smaller modules (`_validation.py`, `_data_loader.py`, `_display_utils.py`) to reduce complexity.

**Next Steps:**
*   **Phase 1, Step 1.4: Write unit tests for `src/git_dataframe_tools/cli/scoreboard.py`.** (This is already done as part of debugging)
*   **Phase 1, Step 1.5: Write unit tests for `src/git_dataframe_tools/logger.py`.**
*   **Phase 2: Address Missed Lines in Other Modules.**
*   **Phase 3: Set Coverage Target and Final Verification.**