# git-extract-commits CLI Runbook

This runbook demonstrates how to use the `git-extract-commits` command-line interface to extract Git commit data to a Parquet file, and then how to analyze that data using DuckDB.

## 1. `git-extract-commits` CLI Usage

The `git-extract-commits` CLI leverages the `git2df` library to extract commit information from a Git repository and save it as a Parquet file. This file can then be easily queried using tools like DuckDB.

### Installation

Ensure you have the `git-scoreboard` project installed and the `git2df` library is available in your Python environment. You can run the CLI using `python src/git_scoreboard/git_extract_commits.py`.

### Basic Usage

To extract all commit data from the current Git repository and save it to `commits.parquet`:

```bash
python src/git_extract_commits.py --output commits.parquet
```

To extract from a specific repository:

```bash
python src/git_extract_commits.py --repo-path /path/to/your/repo --output repo_commits.parquet
```

### Filtering Commits

The CLI supports various filtering options, mirroring `git log` functionality.

#### Filter by Date (`--since`, `--until`)

Extract commits made between specific dates (inclusive):

```bash
# Commits since January 1, 2023
python src/git_extract_commits.py --since 2023-01-01 --output commits_since_2023.parquet

# Commits until December 31, 2023
python src/git_extract_commits.py --until 2023-12-31 --output commits_until_2023.parquet

# Commits in June 2023
python src/git_extract_commits.py --since 2023-06-01 --until 2023-06-30 --output commits_june_2023.parquet
```

#### Filter by Author (`--author`)

Extract commits by a specific author (case-insensitive match):

```bash
python src/git_extract_commits.py --author "John Doe" --output john_doe_commits.parquet
```

#### Filter by Commit Message (`--grep`)

Extract commits whose messages contain a specific pattern:

```bash
python src/git_extract_commits.py --grep "feature" --output feature_commits.parquet
```

#### Filter for Merged Commits Only (`--merged-only`)

Extract only commits that have been merged into the current branch:

```bash
python src/git_extract_commits.py --merged-only --output merged_only_commits.parquet
```

#### Filter by Included/Excluded Paths (`--include-paths`, `--exclude-paths`)

Extract commits affecting specific files or directories, or exclude them. Use space-separated paths/patterns.

```bash
# Commits affecting only files in the 'src/' directory
python src/git_extract_commits.py --include-paths src/ --output src_commits.parquet

# Commits excluding files in the 'docs/' directory
python src/git_extract_commits.py --exclude-paths docs/ --output no_docs_commits.parquet

# Commits affecting specific files
python src/git_extract_commits.py --include-paths src/git2df/__init__.py src/git2df/backends.py --output specific_files_commits.parquet
```

#### Combined Filters

You can combine multiple filters:

```bash
python src/git_extract_commits.py \
    --since 2023-01-01 \
    --until 2023-12-31 \
    --author "Jane Smith" \
    --grep "bugfix" \
    --include-paths src/ \
    --output jane_bugfixes_2023_src.parquet
```

## 2. Analyzing Parquet Data with DuckDB

DuckDB is an in-process SQL OLAP database management system. It's excellent for querying Parquet files directly.

### Installation

First, install DuckDB (if you haven't already):

```bash
pip install duckdb
```

### Basic DuckDB Usage

Start the DuckDB CLI:

```bash
duckdb
```

Once in the DuckDB prompt, you can query your Parquet file. Let's assume you've generated `commits.parquet`.

```sql
-- Load the Parquet file as a table
SELECT * FROM 'commits.parquet' LIMIT 5;
```

### Mirroring Common Git Commands with SQL

Here are some examples of how to use SQL with DuckDB to get insights similar to common `git` commands.

#### `git shortlog -sn` (Total Commits by Author)

```sql
SELECT
    author_name,
    COUNT(DISTINCT commit_hash) AS total_commits,
    SUM(additions) AS total_additions,
    SUM(deletions) AS total_deletions
FROM 'commits.parquet'
GROUP BY author_name
ORDER BY total_commits DESC;
```

#### `git log --author="<author>"` (Commits by a Specific Author)

```sql
SELECT
    commit_hash,
    commit_date,
    commit_message
FROM 'commits.parquet'
WHERE author_name = 'John Doe'
ORDER BY commit_date DESC
LIMIT 10;
```

#### `git log --grep="<pattern>"` (Commits with Specific Message Pattern)

```sql
SELECT
    commit_hash,
    author_name,
    commit_date,
    commit_message
FROM 'commits.parquet'
WHERE commit_message ILIKE '%feature%'
ORDER BY commit_date DESC
LIMIT 10;
```

#### `git log --since="<date>" --until="<date>"` (Commits in a Date Range)

```sql
SELECT
    commit_hash,
    author_name,
    commit_date,
    commit_message
FROM 'commits.parquet'
WHERE commit_date >= '2023-06-01' AND commit_date < '2023-07-01'
ORDER BY commit_date DESC
LIMIT 10;
```

#### `git show <commit_hash>` (Files Changed in a Specific Commit)

```sql
SELECT
    file_paths,
    change_type,
    additions,
    deletions
FROM 'commits.parquet'
WHERE commit_hash = 'your_commit_hash_here'; -- Replace with an actual commit hash
```

#### Top N Most Changed Files

```sql
SELECT
    file_paths,
    SUM(additions + deletions) AS total_changes
FROM 'commits.parquet'
GROUP BY file_paths
ORDER BY total_changes DESC
LIMIT 10;
```

This runbook provides a solid foundation for extracting and analyzing your Git commit data using `git-extract-commits` and DuckDB.
