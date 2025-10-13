# Plan for Low-Effort Code Improvements

This document outlines the plan to address the low-effort tasks from `CODE_IMPROVEMENTS.md`.

## 1. Consistent Date Handling in `GitAnalysisConfig` (Effort: 1)

*   **Goal:** Ensure `start_date` and `end_date` are consistently `datetime.date` objects or `None`.
*   **File to modify:** `src/git_dataframe_tools/config_models.py`
*   **Steps:**
    1.  In the `__post_init__` of `GitAnalysisConfig`, ensure that `_start_date_str` and `_end_date_str` are parsed into `datetime.date` objects and assigned to `start_date` and `end_date`.
    2.  Remove any `isinstance` checks for `start_date` and `end_date` in `get_analysis_description` and other methods, as the types will now be consistent.
    3.  Run `uv run pytest` to ensure no regressions.

## 2. Generic Decile Calculation (Effort: 2)

*   **Goal:** Make the `_calculate_deciles` function in `git_stats_pandas.py` more generic.
*   **File to modify:** `src/git_dataframe_tools/git_stats_pandas.py`
*   **Steps:**
    1.  Refactor `_calculate_deciles` to accept a column name as a parameter.
    2.  Update the calls to `_calculate_deciles` to pass the column names (`total` and `commits`).
    3.  Run `uv run pytest tests/test_git_stats_pandas.py` to ensure correctness.

## 3. Improve `_parse_period_string` Regex (Effort: 2)

*   **Goal:** Make the date parsing in `config_models.py` more flexible.
*   **File to modify:** `src/git_dataframe_tools/config_models.py`
*   **Steps:**
    1.  Update the regex in `_parse_period_string` to handle singular vs. plural units (e.g., "month" vs "months").
    2.  Add more test cases to `tests/test_config_models_period_parsing.py` to cover the new variations.
    3.  Run `uv run pytest tests/test_config_models_period_parsing.py` to verify the changes.

## 4. Prioritize Explicit String Splitting (Effort: 2)

*   **Goal:** Improve readability and robustness of parsing logic by using string splitting instead of complex regex where appropriate.
*   **File to modify:** `src/git2df/git_parser/_commit_metadata_parser.py`
*   **Steps:**
    1.  Review the parsing functions in `_commit_metadata_parser.py`.
    2.  Identify areas where complex regex is used for parsing structured `git log` output.
    3.  Refactor the code to use `str.split()` with the known delimiters (`@@@COMMIT@@@`, `@@@FIELD@@@`, etc.) instead of regex.
    4.  Run `uv run pytest tests/test_git2df_parser.py` to ensure the output remains the same.

## Final Verification Steps:

1.  Run `uv run pytest` to execute the entire test suite.
2.  Run `uv run ruff check .` to check for linting issues.
3.  Run `uv run mypy .` to check for type-checking issues.
4.  Run `uv run radon cc . -na` to check cyclomatic complexity.
5.  Run `uv run pytest` again to confirm all tests still pass after quality checks.