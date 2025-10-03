## Refactoring Plan: Project Structure and CLI Organization

This plan outlines the steps to reorganize the project's directory structure, rename the main application package, and consolidate CLI entry points for improved clarity and maintainability. **Crucially, after each step, relevant tests will be refactored and run to ensure they pass before proceeding.**

**Goal:**
*   Rename the `git_scoreboard` Python package to `git_dataframe_tools`.
*   Move CLI entry point scripts (`git_df.py`, `scoreboard.py`) into a `cli` subdirectory within the new `git_dataframe_tools` package.
*   Update all internal references, packaging configuration, and tests to reflect these changes.

---

**Phase 0: Setup Refactoring Branch**

**Objective:** Create and switch to a dedicated branch for this refactoring.

*   **Step 0.1: Create and switch to a new branch.**
    *   Command: `git checkout -b refactor/cli-structure`
    *   Verification: `git branch` shows `refactor/cli-structure` as the current branch.
    *   **Test:** Run all tests. (Expected to pass, as no code changes have been made yet).

---

**Phase 1: Rename Main Application Package and Reorganize CLIs**

**Objective:** Rename the `src/git_scoreboard` directory to `src/git_dataframe_tools` and move CLI scripts into a `cli` subdirectory.

*   **Step 1.1: Rename the package directory.**
    *   Command: `mv src/git_scoreboard src/git_dataframe_tools`
    *   Verification: Confirm `src/git_dataframe_tools` exists and `src/git_scoreboard` does not.
    *   **Test Refactoring:**
        *   **Identify affected tests:** All tests importing from `git_scoreboard.*`.
        *   **Update imports:** Change `from git_scoreboard...` to `from git_dataframe_tools...` in all test files.
    *   **Test:** Run all tests. (Expected to pass after import updates).

*   **Step 1.2: Create the `cli` subdirectory.**
    *   Command: `mkdir src/git_dataframe_tools/cli`
    *   Verification: Confirm `src/git_dataframe_tools/cli` exists.
    *   **Test:** Run all tests. (Expected to pass, as this is a directory creation).

*   **Step 1.3: Move CLI scripts into the `cli` subdirectory.**
    *   Command: `mv src/git_dataframe_tools/git_df.py src/git_dataframe_tools/cli/git_df.py`
    *   Command: `mv src/git_dataframe_tools/scoreboard.py src/git_dataframe_tools/cli/scoreboard.py`
    *   Verification: Confirm scripts are in the new location.
    *   **Test Refactoring:**
        *   **Identify affected tests:** Tests that directly call `git-df` or `git-scoreboard` via `sys.executable -m src.git_scoreboard...`.
        *   **Update paths:** Change `src.git_scoreboard.git_df` to `src.git_dataframe_tools.cli.git_df` and `src.git_scoreboard.scoreboard` to `src.git_dataframe_tools.cli.scoreboard` in test commands.
    *   **Test:** Run all tests. (Expected to pass after path updates).

---

**Phase 2: Update Packaging Configuration (`pyproject.toml`)**

**Objective:** Adjust `pyproject.toml` to reflect the new package name and CLI entry points.

*   **Step 2.1: Update `[tool.setuptools.packages.find]` `where` clause.**
    *   Instruction: Read `pyproject.toml`, then replace `where = ["src"]` with `where = ["src", "src/git_dataframe_tools"]` (or similar to ensure both `git2df` and `git_dataframe_tools` are found).
    *   Verification: Manually inspect `pyproject.toml`.
    *   **Test:** Run all tests. (Expected to pass).

*   **Step 2.2: Update `[project.scripts]` entry points.**
    *   Instruction:
        *   Change `git-scoreboard = "git_scoreboard.scoreboard:main"` to `git-scoreboard = "git_dataframe_tools.cli.scoreboard:main"`.
        *   Change `git-df = "git_scoreboard.git_df:main"` to `git-df = "git_dataframe_tools.cli.git_df:main"`.
    *   Verification: Manually inspect `pyproject.toml`.
    *   **Test:** Run all tests. (Expected to pass).

---

**Phase 3: Update Internal Python Imports**

**Objective:** Modify all Python files to use the new package name (`git_dataframe_tools`) and the new paths for CLI scripts.

*   **Step 3.1: Update imports in `src/git_dataframe_tools/cli/git_df.py`.**
    *   Instruction: Change `from git_scoreboard.logger import setup_logging` to `from git_dataframe_tools.logger import setup_logging`.
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run all tests.

*   **Step 3.2: Update imports in `src/git_dataframe_tools/cli/scoreboard.py`.**
    *   Instruction: Change `from git_scoreboard.logger import setup_logging` to `from git_dataframe_tools.logger import setup_logging`.
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...`.
    *   Instruction: Change `import git_scoreboard.git_stats_pandas as stats_module` to `import git_dataframe_tools.git_stats_pandas as stats_module`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run all tests.

*   **Step 3.3: Update imports in `src/git_dataframe_tools/config_models.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...` (if any self-referential imports exist).
    *   Verification: Manually inspect the file.
    *   **Test:** Run all tests.

*   **Step 3.4: Update imports in `src/git_dataframe_tools/git_stats_pandas.py`.**
    *   Instruction: Change `from .config_models import ...` to `from git_dataframe_tools.config_models import ...` (or ensure relative imports are correct).
    *   Verification: Manually inspect the file.
    *   **Test:** Run all tests.

*   **Step 3.5: Update imports in `src/git_dataframe_tools/logger.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...` (if applicable).
    *   Verification: Manually inspect the file.
    *   **Test:** Run all tests.

---

**Phase 4: Refactor Tests (Detailed)**

**Objective:** Update all test files to reflect the new package name and CLI script locations, ensuring tests pass after each update.

*   **Step 4.1: Update `tests/test_failing_case.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_failing_case.py`.

*   **Step 4.2: Update `tests/test_git2df_backends.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...` (if applicable).
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git2df_backends.py`.

*   **Step 4.3: Update `tests/test_git2df_cli_utils.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...` (if applicable).
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git2df_cli_utils.py`.

*   **Step 4.4: Update `tests/test_git2df_dataframe_builder.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...` (if applicable).
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git2df_dataframe_builder.py`.

*   **Step 4.5: Update `tests/test_git2df_parser.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...` (if applicable).
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git2df_parser.py`.

*   **Step 4.6: Update `tests/test_git2df_public_api.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...` (if applicable).
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git2df_public_api.py`.

*   **Step 4.7: Update `tests/test_git_df.py`.**
    *   Instruction: Change `sys.executable, "-m", "src.git_scoreboard.git_df"` to `sys.executable, "-m", "src.git_dataframe_tools.cli.git_df"`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git_df.py`.

*   **Step 4.8: Update `tests/test_git_integration.py`.**
    *   Instruction: Change `sys.executable, "-m", "src.git_scoreboard.git_df"` to `sys.executable, "-m", "src.git_dataframe_tools.cli.git_df"`.
    *   Instruction: Change `sys.executable, "-m", "src.git_scoreboard.scoreboard"` to `sys.executable, "-m", "src.git_dataframe_tools.cli.scoreboard"`.
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git_integration.py`.

*   **Step 4.9: Update `tests/test_git_interaction.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git_interaction.py`.

*   **Step 4.10: Update `tests/test_git_stats_pandas.py`.**
    *   Instruction: Change `from git_scoreboard.git_stats_pandas import ...` to `from git_dataframe_tools.git_stats_pandas import ...`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git_stats_pandas.py`.

*   **Step 4.11: Update `tests/test_scoreboard.py`.**
    *   Instruction: Change `from git_scoreboard.config_models import ...` to `from git_dataframe_tools.config_models import ...`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_scoreboard.py`.

---

**Phase 5: Final Verification and Cleanup**

**Objective:** Ensure all changes are correct and the project remains functional.

*   **Step 5.1: Run all tests.**
    *   Command: `uv run pytest tests/`
    *   Verification: All tests must pass.

*   **Step 5.2: Run `ruff check .` and `black .`.**
    *   Command: `uv run ruff check .`
    *   Command: `uv run black .`
    *   Verification: No errors from `ruff`, and `black` reports no files changed.

*   **Step 5.3: Update `README.md` and `APPENDIX-DUCKDB.md` (if necessary).**
    *   Instruction: Ensure any hardcoded paths or package names are updated.
    *   Verification: Manually inspect the files.

*   **Step 5.4: Commit all changes.**
    *   Command: `git add .`
    *   Command: `git commit -m "feat: Reorganize project structure and CLIs"`
    *   Verification: `git status` shows a clean working tree.

---
