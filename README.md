# Git Scoreboard

Git Scoreboard is a project designed to analyze Git repository history, providing powerful insights into author contributions and code changes. It's built on a modular architecture, featuring a core library (`git2df`), a data extraction CLI (`git-df`), and the main analysis CLI (`git-scoreboard`).

## Project Structure

*   **`git2df` (Library):** The robust Python library for extracting detailed Git commit data into Pandas DataFrames. It's the engine that powers data acquisition for analytical tasks.
*   **`git-df` (CLI):** Your go-to command-line tool for efficiently extracting Git commit data and saving it as versioned Parquet files. Perfect for creating reproducible datasets for analysis.
*   **`git-scoreboard` (CLI):** The primary analysis tool. It takes Git commit data and transforms it into actionable insights, ranking authors and highlighting contribution patterns.

## Features

### `git2df` Library: The Analytical Foundation

*   **Deep Dive into Git History:** Extracts comprehensive commit information, including hash, parent hash, author details, commit date, message, and granular file-level changes (additions, deletions, change type, file paths).
*   **Structured Data for Analysis:** Delivers data in a commit-centric Pandas DataFrame, where each row precisely details a single file change within a commit.
*   **Flexible Filtering:** Supports a wide array of filtering options (since, until, author, grep, merged-only, include/exclude paths) to pinpoint the exact data you need.

### `git-df` CLI: Your Data Extraction Powerhouse

*   **Effortless Data Export:** Quickly extracts Git commit data and saves it to highly efficient Parquet files, optimized for large repositories and subsequent analytical workflows.
*   **Built-in Data Provenance:** Automatically embeds `data_version` and `description` metadata directly into your Parquet files, ensuring data integrity and compatibility for future use.
*   **Cross-Environment Compatibility:** Designed for portable execution, ensuring your data extraction process is consistent wherever you run it.

### `git-scoreboard` CLI: Unlock Your Team's Contribution Story

**Get instant insights into who's driving change and how your team contributes!**

*   **Flexible Data Source:** Analyze directly from any Git repository, or supercharge your workflow by loading pre-extracted data from a `git-df` generated Parquet file (using the `--df-path` option).
*   **Smart Data Compatibility:** Automatically verifies the `data_version` of loaded Parquet files, safeguarding your analysis from outdated or incompatible data. Need to proceed anyway? Use `--force-version-mismatch`.
*   **Clear Author Rankings:** See at a glance who's leading in lines added, deleted, and total commits.
*   **Contribution Hotspots:** Understand the distribution of effort with intuitive decile analysis for both diff size and commit count.
*   **Targeted Insights:** Focus on specific authors or contribution types with powerful filtering capabilities.

## Installation

To install the project and its dependencies, it's recommended to use `uv`:

```bash
uv pip install -e .
```

This will install the `git2df` library and make the `git-df` and `git-scoreboard` CLIs available in your environment.

## Usage

### `git-df` (Git Data Extractor)

Extracts Git commit data to a Parquet file.

```bash
git-df <repo_path> --output <output_file.parquet> [OPTIONS]
```

**Example:** Extract all commits from the current directory to `commits.parquet`.

```bash
git-df . --output commits.parquet --since "1 year ago" --until "now"
```

**Options:**

*   `repo_path`: Path to the Git repository (default: current directory).
*   `-S, --since`: Start date for analysis (e.g., "2023-01-01", "3 months ago").
*   `-U, --until`: End date for analysis (e.g., "2023-03-31", "now").
*   `-a, --author`: Filter by author name or email (e.g., "John Doe", "john@example.com").
*   `-g, --grep`: Filter by commit message (e.g., "fix", "feature").
*   `-m, --merges`: Only include merge commits.
*   `-p, --path`: Include only changes in specified paths (can be used multiple times).
*   `-x, --exclude-path`: Exclude changes in specified paths (can be used multiple times).
*   `-o, --output`: Output Parquet file path (required).

### `git-scoreboard` (Git Author Scoreboard)

Analyzes Git commit data and ranks authors.

```bash
git-scoreboard <repo_path> [OPTIONS]
```

**Example:** Analyze commits from a repository, loading data from a Parquet file.

```bash
git-scoreboard --df-path commits.parquet --since "1 year ago" --until "now"
```

**Example:** Analyze commits directly from a Git repository.

```bash
git-scoreboard . --since "6 months ago"
```

**Options:**

*   `repo_path`: Path to the Git repository (default: current directory). *Ignored if `--df-path` is used.*
*   `--df-path`: Path to a Parquet file containing pre-extracted Git commit data (e.g., from `git-df`).
*   `--force-version-mismatch`: Proceed with analysis even if the DataFrame version does not match the expected version.
*   `-S, --since`: Start date for analysis.
*   `-U, --until`: End date for analysis.
*   `-a, --author`: Filter by author name or email.
*   `-m, --me`: Filter by current git user.
*   `--merges`: Only include merge commits.
*   `-p, --path`: Include only changes in specified paths.
*   `-x, --exclude-path`: Exclude changes in specified paths.
*   `--default-period`: Default period if `--since` or `--until` are not specified (e.g., "3 months").

## DataFrame Structure

The DataFrame returned by `git2df` and saved by `git-df` includes the following columns, with one row per file change per commit:

*   `commit_hash`: SHA of the commit.
*   `parent_hash`: Optional; parent SHA.
*   `author_name`: Name of the commit author.
*   `author_email`: Email of the commit author.
*   `commit_date`: Timestamp of the commit (author date or committer date).
*   `file_paths`: Path of the file touched in this change.
*   `change_type`: Type of change (e.g., "A" for added, "M" for modified, "D" for deleted).
*   `additions`: Number of lines added in this specific file change.
*   `deletions`: Number of lines removed in this specific file change.
*   `commit_message`: Full commit message.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
