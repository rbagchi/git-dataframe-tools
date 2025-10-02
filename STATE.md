## Current Work: Refactoring for Pandas Integration and Circular Import Resolution

I am currently refactoring the `git-scoreboard` project to enable the Pandas-based statistics module (`git_stats_pandas.py`) and resolve circular import dependencies.

**Recent Changes & Issues:**

1.  **Attempted Pandas Integration:** Modified `scoreboard.py` to import and use functions from `git_stats_pandas.py`.
2.  **Circular Import Introduced:** Moving `GitAnalysisConfig` class to `config_models.py` without its associated methods caused `AttributeError`s across many tests, indicating a circular import problem.

**Current State of Tests (as of latest test run):**

All tests are passing.

**Completed Steps:**

1.  **Resolved Circular Import & `AttributeError`s:**
    *   Moved all methods belonging to `GitAnalysisConfig` (e.g., `_get_date_range`, `get_git_log_data`, `_get_current_git_user`, etc.) from `scoreboard.py` to `config_models.py`.
    *   Moved utility functions like `Colors` and `print_*` functions from `scoreboard.py` to `config_models.py`.
    *   Updated all necessary imports in `config_models.py`, `scoreboard.py`, `git_stats_pandas.py`, and `git_stats.py` to support these moved methods and functions.
    *   Cleaned up `scoreboard.py` by removing the moved methods and redundant imports.
    *   Updated `git_stats_pandas.py` and `git_stats.py` to import `GitAnalysisConfig` and `_parse_period_string` from `config_models.py`.
    *   Fixed all related test failures in `test_failing_case.py`, `test_git_integration.py`, `test_git_interaction.py`, and `test_scoreboard.py`.

2.  **Implemented Module Switching:**
    *   Standardized function names and signatures in `git_stats.py` and `git_stats_pandas.py`.
    *   Added a `--pandas` command-line option to `scoreboard.py`.
    *   Updated `scoreboard.py` to dynamically select the statistics module based on the `--pandas` argument.
    *   Updated test files (`tests/test_compatibility.py` and `tests/test_git_stats_pandas.py`) to reflect the new standardized function names and interfaces.

3.  **Surveyed Command-Line Options:**
    *   Renamed `--start` to `--since` and `-s` to `-S`.
    *   Renamed `--end` to `--until` and `-e` to `-U`.
    *   Renamed `--merged-only` to `--merges`.
    *   Updated `scoreboard.py` to use the new argument names.

**Next Steps:**

All planned work has been completed. The project is in a stable state.
