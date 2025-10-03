## Completed Work: Refactoring Project Structure and CLI Organization

I have completed the refactoring of the project structure to rename the main application package from `git_scoreboard` to `git_dataframe_tools` and move CLI entry points into a `cli` subdirectory, following the plan outlined in `CLI-REFACTORING.md`.

**Completed Steps:**

*   **Phase 0: Setup Refactoring Branch**
    *   Created and switched to `refactor/cli-structure` branch.

*   **Phase 1: Rename Main Application Package and Reorganize CLIs**
    *   **Step 1.1: Rename the package directory.**
        *   `src/git_scoreboard` renamed to `src/git_dataframe_tools`.
        *   Updated imports in all test files.
    *   **Step 1.2: Create the `cli` subdirectory.**
        *   `src/git_dataframe_tools/cli` directory created.
    *   **Step 1.3: Move CLI scripts into the `cli` subdirectory.**
        *   `src/git_dataframe_tools/git_df.py` moved to `src/git_dataframe_tools/cli/git_df.py`.
        *   `src/git_dataframe_tools/scoreboard.py` moved to `src/git_dataframe_tools/cli/scoreboard.py`.
        *   Updated paths in test commands.

*   **Phase 2: Update Packaging Configuration and Fix Imports**
    *   Added `__init__.py` to `src/git_dataframe_tools/cli` to make it a package.
    *   Updated `pyproject.toml` to correctly discover the new package structure.
    *   Reinstalled the package in editable mode using `uv pip install -e .`.
    *   Fixed remaining imports from `git_scoreboard` to `git_dataframe_tools` in the application code.

**Completion:**

All tests are now passing, and the refactoring is complete. The project structure is now cleaner and more consistent.
