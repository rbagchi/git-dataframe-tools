# Regenerating Golden Files

Golden files are used in our test suite (specifically for `tests/test_git2df_parser.py`) to ensure that our parsing logic consistently produces the expected output. These files consist of:
- `.log` files: Contain raw `git log` output with specific delimiters.
- `.json` files: Contain the expected parsed data in JSON format, corresponding to their `.log` counterparts.

When the parsing logic in `src/git2df/git_parser.py` changes, or if the format of the raw `git log` output (e.g., delimiters) is intentionally modified, the `.json` golden files may become outdated, leading to test failures. In such cases, you need to regenerate the `.json` golden files.

## How to Regenerate Golden Files

To regenerate the `.json` golden files, follow these steps:

1.  **Ensure your parsing logic is correct:** Before regenerating, make sure any changes to `src/git2df/git_parser.py` are intended and functionally correct.

2.  **Create and run the regeneration script:**
    Create a Python script (e.g., `regenerate_golden_files.py`) in the project root with the following content:

    ```python
    import json
    from pathlib import Path
    from datetime import datetime, timezone
    from git2df.git_parser import _parse_git_data_internal
    import logging

    # Configure logging to output debug messages to console
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    def regenerate_golden_files():
        data_dir = Path(__file__).parent / "tests" / "data"
        for log_file in data_dir.glob("*.log"):
            json_file = log_file.with_suffix(".json")
            logger.info(f"Processing {log_file}...")
            with open(log_file, "r") as f:
                git_log_output = f.read().splitlines()

            parsed_data = _parse_git_data_internal(git_log_output)

            # Convert datetime objects to ISO format strings for JSON serialization
            for item in parsed_data:
                if "commit_date" in item and isinstance(item["commit_date"], datetime):
                    item["commit_date"] = item["commit_date"].isoformat()

            with open(json_file, "w") as f:
                json.dump(parsed_data, f, indent=4)
            logger.info(f"Generated {json_file}")

    if __name__ == "__main__":
        regenerate_golden_files()
    ```

3.  **Execute the script:**
    Run the script from your project root using `uv`:

    ```bash
    uv run python regenerate_golden_files.py
    ```

    This will read all `.log` files in `tests/data/`, parse them using the current `_parse_git_data_internal` logic, and overwrite the corresponding `.json` files with the new expected output.

4.  **Verify changes:**
    After regeneration, run the test suite to ensure all tests pass with the updated golden files:

    ```bash
    uv run pytest
    ```

    If all tests pass, the golden files have been successfully regenerated and are in sync with your current parsing logic.

5.  **Remove the regeneration script:**
    Once you've confirmed the golden files are updated and tests pass, you can remove the temporary regeneration script:

    ```bash
    rm regenerate_golden_files.py
    ```
