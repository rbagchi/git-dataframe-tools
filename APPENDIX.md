# Appendix: Querying Git Data with DuckDB (Proof of Concept)

This appendix demonstrates a proof-of-concept workflow for extracting Git commit data using the `git-df` CLI and then performing SQL queries directly on the resulting Parquet file using the `duckdb` command-line interface.

This approach allows for powerful, ad-hoc analysis of your Git history without needing to write Python scripts for every query.

## Prerequisites

*   **`git-dataframe-tools` installed:** Ensure you have the `git-df` CLI available in your environment.
*   **`duckdb` installed:** You can install the `duckdb` Python package, which includes the `duckdb` CLI, or install the `duckdb` CLI separately.

    ```bash
    uv pip install duckdb
    ```

## Step 1: Extract Git Data to a Parquet File using `git-df`

First, we'll use `git-df` to extract commit data from a Git repository into a Parquet file. Navigate to the root of the Git repository you wish to analyze in your terminal.

```bash
# Example: Extract all commits from the current directory for the last year
git-df . --output git_commits.parquet --since "1 year ago" --until "now" -v
```

This command will create a file named `git_commits.parquet` in your current directory, containing the extracted Git history.

## Step 2: Query the Parquet File using `duckdb` CLI

Now, you can use the `duckdb` command-line interface to directly query the `git_commits.parquet` file using SQL.

1.  **Start the `duckdb` CLI:**

    ```bash
    duckdb
    ```

    You will see a `D> ` prompt.

2.  **Execute SQL queries:** You can now run SQL queries directly against your Parquet file. DuckDB treats Parquet files as tables.

    ```sql
    -- Example Query 1: Show the schema of the Parquet file
    D> DESCRIBE 'git_commits.parquet';

    -- Example Query 2: Count the total number of unique commits
    D> SELECT COUNT(DISTINCT commit_hash) FROM 'git_commits.parquet';

    -- Example Query 3: Find the top 5 authors by total lines added
    D> SELECT
    D>   author_name,
    D>   SUM(additions) AS total_additions
    D> FROM 'git_commits.parquet'
    D> GROUP BY author_name
    D> ORDER BY total_additions DESC
    D> LIMIT 5;

    -- Example Query 4: Get the number of commits per month
    D> SELECT
    D>   strftime(commit_date, '%Y-%m') AS commit_month,
    D>   COUNT(DISTINCT commit_hash) AS num_commits
    D> FROM 'git_commits.parquet'
    D> GROUP BY commit_month
    D> ORDER BY commit_month;

    -- Example Query 5: Find the top 3 files with the most deletions
    D> SELECT
    D>   file_paths,
    D>   SUM(deletions) AS total_deletions
    D> FROM 'git_commits.parquet'
    D> GROUP BY file_paths
    D> ORDER BY total_deletions DESC
    D> LIMIT 3;
    ```

3.  **Exit `duckdb` CLI:**

    ```sql
    D> .exit
    ```

This proof of concept demonstrates the power and flexibility of combining `git-df` for structured data extraction with `duckdb` for interactive SQL-based analysis of your Git history.
