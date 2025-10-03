## Migration Plan: `subprocess` to `GitPython`

This plan outlines the steps to migrate from using `subprocess` to call `git` to using the `GitPython` library. This will make the code more robust, readable, and maintainable.

**Goal:**
*   Replace all `subprocess` calls to `git` with `GitPython` equivalents.
*   Ensure all tests pass after each step.
*   Add `GitPython` as a project dependency.

---

**Phase 0: Setup**

*   **Step 0.1: Create and switch to a new branch.**
    *   Command: `git checkout -b feat/migrate-to-gitpython`
    *   Verification: `git branch` shows `feat/migrate-to-gitpython` as the current branch.

*   **Step 0.2: Add `GitPython` dependency.**
    *   Instruction: Add `GitPython` to the `dependencies` list in `pyproject.toml`.
    *   Command: `uv pip install -e .` to install the new dependency.
    *   Verification: `uv pip list` shows `gitpython`.
    *   **Test:** Run all tests. (Expected to pass, as no code has been changed yet).

---

**Phase 1: Refactor `config_models.py`**

*   **Objective:** Replace `subprocess` calls in `src/git_dataframe_tools/config_models.py` used to get git config values.
*   **Step 1.1: Refactor `_get_current_user_name` and `_get_current_user_email`.**
    *   Instruction: Modify the functions to use `git.Repo(...).config_reader().get_value('user', 'name')` and `...get_value('user', 'email')`.
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git_interaction.py`. Then run all tests.

---

**Phase 2: Refactor `git_cli_utils.py`**

*   **Objective:** Replace the main `git` subprocess call in `src/git2df/git_cli_utils.py`. This is the core function for getting the git log.
*   **Step 2.1: Refactor `get_git_log`.**
    *   Instruction: This is a significant change. The `subprocess.run(['git', 'log', ...])` call will be replaced with `git.Repo(...).iter_commits(...)`. The arguments will need to be mapped from the `git log` command-line options to the `iter_commits` parameters.
    *   Verification: This will be verified by the tests.
    *   **Test:** Run `uv run pytest tests/test_git2df_cli_utils.py`. Then run all tests.

---

**Phase 3: Refactor `backends.py`**

*   **Objective:** Replace `subprocess` calls in `src/git2df/backends.py`.
*   **Step 3.1: Refactor git operations.**
    *   Instruction: Replace `subprocess.run(['git', ...])` calls with their `GitPython` equivalents (e.g., for checking if a directory is a git repo).
    *   Verification: Manually inspect the file.
    *   **Test:** Run `uv run pytest tests/test_git2df_backends.py`. Then run all tests.

---

**Phase 4: Final Verification and Cleanup**

*   **Step 4.1: Run all tests.**
    *   Command: `uv run pytest tests/`
    *   Verification: All tests must pass.
*   **Step 4.2: Run `ruff check .` and `black .`.**
    *   Command: `uv run ruff check .`
    *   Command: `uv run black .`
    *   Verification: No errors from `ruff`, and `black` reports no files changed.
*   **Step 4.3: Remove unused `subprocess` imports.**
    *   Instruction: Search for and remove any `import subprocess` statements that are no longer needed.
    *   Verification: Manually inspect the files.
*   **Step 4.4: Commit all changes.**
    *   Command: `git add .`
    *   Command: `git commit -m "feat: Migrate from subprocess to GitPython"`
    *   Verification: `git status` shows a clean working tree.
