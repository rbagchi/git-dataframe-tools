# Test Suite Improvement Plan

This document outlines a series of actionable steps to improve the robustness, maintainability, and clarity of the test suite, with a focus on reducing brittle mocks.

## 1. Consolidate Git Repository Setup with a `pytest` Fixture

**Goal:** Eliminate redundant code for creating temporary Git repositories in tests.

**Actionable Steps:**

1.  Create a file `tests/conftest.py` if it doesn't already exist.
2.  In `tests/conftest.py`, create a `pytest` fixture named `git_repo`.
3.  This fixture should:
    *   Create a new temporary directory.
    *   Initialize a Git repository in it.
    *   Optionally, allow for pre-populating the repository with some initial commits.
    *   `yield` the path to the repository.
    *   After the test, clean up the temporary directory.
4.  Refactor existing tests in `tests/test_git_integration.py` and other relevant files to use the `git_repo` fixture instead of manual setup and teardown.

## 2. Refactor `dulwich` Backend Tests to Use a Real Repository

**Goal:** Replace complex and brittle mocks in `tests/test_git2df_dulwich_backend.py` with a real `dulwich` repository.

**Actionable Steps:**

1.  Create a new `pytest` fixture (e.g., `dulwich_repo`) that sets up a temporary directory and initializes a `dulwich` repository.
2.  In your test setup (or within the fixture), use the `dulwich` API to make actual commits with files. This will generate real `Commit`, `Tree`, and `Blob` objects.
3.  Modify the tests in `tests/test_git2df_dulwich_backend.py` to use this fixture.
4.  Instead of mocking `dulwich.diff_tree.tree_changes`, call it with the real objects from your test repository and assert against the actual output. This will make your tests more resilient to changes in the `dulwich` library.

## 3. Externalize Test Data with "Golden Files"

**Goal:** Move large, hardcoded test data (like Git log strings) out of the test files and into a dedicated data directory.

**Actionable Steps:**

1.  Create a new directory: `tests/data/`.
2.  For `tests/test_git2df_parser.py`, identify the raw Git log strings used as input.
3.  For each test case, create a "golden file" in `tests/data/` (e.g., `tests/data/parser_input_basic.log`).
4.  Create corresponding files for the expected output (e.g., `tests/data/parser_output_basic.csv`).
5.  Create a `pytest` fixture that can read these file pairs.
6.  Use `pytest.mark.parametrize` to run the parser test against all the input/output pairs in the `tests/data/` directory. This is known as a "characterization test" or "golden master test".

## 4. Refine Mocking Strategy for CLI and API Tests

**Goal:** Reduce the complexity of mocks in higher-level tests.

**Actionable Steps:**

1.  Review tests in `tests/test_git_df_cli.py` and `tests/test_scoreboard.py`.
2.  Identify where you are mocking deep into the application (e.g., mocking functions within the `git2df` library).
3.  Refactor these tests to mock at a higher level. For example, instead of mocking the backend that `get_commits_df` uses, mock `get_commits_df` itself to return a pre-defined Pandas DataFrame.
4.  This will decouple the CLI tests from the implementation details of the data-gathering logic, making them more robust.

## 5. General Test Suite Health

**Goal:** Apply general `pytest` best practices to improve the overall quality of the suite.

**Actionable Steps:**

1.  **Use Parametrization:** In files like `tests/test_config_models_period_parsing.py`, use `pytest.mark.parametrize` to test multiple inputs with the same test function, reducing code duplication.
2.  **Review for Hardcoded Values:** Perform a general review of the test suite for any hardcoded paths, usernames, or other values that could be replaced with fixtures or generated dynamically.
3.  **Ensure Test Isolation:** Double-check that all tests are properly isolated and do not depend on the state left by other tests. The use of fixtures for setup and teardown will help enforce this.
