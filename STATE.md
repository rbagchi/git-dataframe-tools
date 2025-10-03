**Current Work:** Debugging Failing Unit Tests in `tests/test_scoreboard.py`

**Progress:**
*   **Added Code Quality Tools:**
    *   `mypy` for static type checking. All type errors resolved.
    *   `pytest-cov` for test coverage analysis.
    *   `radon` for cyclomatic complexity analysis.
*   **Refactored `src/git_dataframe_tools/cli/git_df.py`:**
    *   Extracted core logic into `run_git_df_cli` for testability.
    *   Wrote unit tests for `run_git_df_cli`, increasing coverage for `git_df.py` to 69%.
    *   Fixed `SystemExit` handling in `git_df_cli` tests.

*   **Debugging `tests/test_scoreboard.py`:**
    *   Identified and addressed several patching issues related to logger and imported functions.
    *   Corrected argument order in test function signatures.
    *   Still working on resolving all failing tests.

**Next Steps:**
*   **Phase 1, Step 1.4: Continue debugging and resolve remaining unit tests for `src/git_dataframe_tools/cli/scoreboard.py`.**
*   **Phase 1, Step 1.5: Write unit tests for `src/git_dataframe_tools/logger.py`.**
*   **Phase 2: Address Missed Lines in Other Modules.**
*   **Phase 3: Set Coverage Target and Final Verification.**