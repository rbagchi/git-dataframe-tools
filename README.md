# Git Scoreboard: Quantify Your Impact. Prove Your Value.

## Stop Guessing. Start Proving.

Ever wondered how to objectively demonstrate your team's (or your own!) impact in a Git repository? `git-scoreboard` is your secret weapon. This command-line tool cuts through the noise, analyzing git history to rank authors by total lines changed, commits, and decile rankings. It's not just about lines of code; it's about **uncovering and validating tangible contributions** that drive your projects forward.

## Quick Start

Get up and running with `git-scoreboard` in minutes!

1.  **Install `git-scoreboard`**:
    ```bash
    pip install git-scoreboard
    ```

2.  **Navigate to any Git repository** on your system:
    ```bash
    cd /path/to/your/git/repo
    ```

3.  **Run your first analysis** (e.g., see team contributions for the last 3 months):
    ```bash
    git-scoreboard
    ```

4.  **See your own contributions** (perfect for that 1:1!):
    ```bash
    git-scoreboard --me
    ```

## Why You Need Git Scoreboard:

*   **Showcase Your Contributions**: Objectively highlight your personal impact and growth over time.
*   **Validate Team Productivity**: Get a clear, data-driven overview of who's contributing what, where, and how much.
*   **Identify Key Players**: Quickly spot top contributors and understand their influence on the codebase.
*   **Track Progress & Velocity**: Monitor team activity and code output across specific date ranges or merged code.
*   **Data-Driven Discussions**: Arm yourself with concrete metrics for performance reviews, team retrospectives, and resource allocation.

## Features

-   **Author Ranking**: Ranks authors based on their total lines changed (additions + deletions).
-   **Detailed Author Stats**: View granular statistics for any author, including lines added, deleted, total diff, commits, and their decile rankings relative to the team.
-   **Flexible Date Range Analysis**: Pinpoint contributions within custom date ranges to align with sprints, quarters, or project milestones.
-   **"Me" Mode**: Instantly see your own contributions – perfect for quick self-assessments or preparing for that 1:1. 
-   **Merged Commits Only**: Focus solely on code that made it to the main branch, reflecting true production impact.
-   **Progress Bar**: Visual progress indicator for large repositories (requires `tqdm`).

## Installation

You can install `git-scoreboard` using pip:

```bash
pip install git-scoreboard
```
*(For best practice, consider installing within a Python [virtual environment](https://docs.python.org/3/library/venv.html).)*

## Usage & Examples (Your Runbook)

Run `git-scoreboard` from within any Git repository.

To see all available options:
```bash
git-scoreboard --help
```

Here are common scenarios and how to execute them:

-   **Scenario: Get a general overview of team contributions for the last 3 months (default).**
    ```bash
    git-scoreboard
    ```

-   **Scenario: Analyze contributions for the last 6 months instead of the default 3 months.**
    ```bash
    git-scoreboard --default-period "6 months"
    ```

-   **Scenario: Analyze contributions for the last 1 year.**
    ```bash
    git-scoreboard --default-period "1 year"
    ```

-   **Scenario: Analyze contributions from a specific start date (e.g., June 1st, 2025) to today.**
    ```bash
    git-scoreboard --since 2025-06-01
    ```

-   **Scenario: Analyze contributions from "last week" to "yesterday".**
    ```bash
    git-scoreboard --since "last week" --until "yesterday"
    ```

-   **Scenario: Analyze contributions from "3 months ago" to "now".**
    ```bash
    git-scoreboard --since "3 months ago" --until "now"
    ```

-   **Scenario: Review team output for a period ending on a specific date (e.g., last 3 months before August 31st, 2025).**
    ```bash
    git-scoreboard --until 2025-08-31
    ```

-   **Scenario: Get the full picture for a specific project phase or quarter (e.g., between June 1st and August 31st, 2025).**
    ```bash
    git-scoreboard --since 2025-06-01 --until 2025-08-31
    ```

-   **Scenario: Deep dive into a specific contributor's output (e.g., "john.doe" by partial name or email match).**
    ```bash
    git-scoreboard --author "john.doe"
    ```

-   **Scenario: Show *your* detailed stats – for that performance review!**
    ```bash
    git-scoreboard --me
    ```

-   **Scenario: See your contributions for a specific date range.**
    ```bash
    git-scoreboard --me --since 2025-06-01
    ```

-   **Scenario: Focus only on production-ready code – analyze commits that have been merged to the main branch.**
    ```bash
    git-scoreboard --merges
    ```

-   **Scenario: See *your* merged contributions only – prove your impact on the main codebase.**
    ```bash
    git-scoreboard --me --merges
    ```

-   **Scenario: Analyze contributions only within the `src/frontend` directory.**
    ```bash
    git-scoreboard --path src/frontend
    ```

-   **Scenario: Analyze contributions in `src/backend` but exclude changes in `src/backend/tests`.**
    ```bash
    git-scoreboard --path src/backend --exclude-path src/backend/tests
    ```

-   **Scenario: Analyze all contributions except those in `docs` or `tests` directories.**
    ```bash
    git-scoreboard --exclude-path docs tests
    ```

-   **Scenario: Use the experimental Pandas-based statistics engine.**
    ```bash
    git-scoreboard --pandas
    ```

### Example: Analyzing the Flask Project

Let's see `git-scoreboard` in action on a popular open-source project like [Flask](https://github.com/pallets/flask).

1.  **Clone the Flask repository** (if you haven't already):
    ```bash
    git clone https://github.com/pallets/flask.git
    cd flask
    ```
    *(Ensure your `git-scoreboard` tool is installed and accessible in your PATH, ideally within an activated virtual environment.)*

2.  **Get the overall scoreboard for Flask's core development over the last year**:
    ```bash
    git-scoreboard --default-period "1 year" --path src/flask
    ```
    *This command will show you the top contributors to Flask's core source code over the past year, ranked by lines changed.*

3.  **Deep dive into a specific core contributor (e.g., "davidism") for their merged contributions**:
    ```bash
    git-scoreboard --author "davidism" --merges --default-period "6 months"
    ```
    *This will provide detailed statistics for "davidism" on code that has been merged into Flask's main branch in the last six months, showcasing their direct impact.*

4.  **Analyze contributions to Flask's documentation**:
    ```bash
    git-scoreboard --path docs --default-period "2 years"
    ```
    *This helps identify who has been most active in maintaining and improving Flask's documentation over a longer period.*

### Arguments

-   `--since`, `-S` (type: `str`): Start date for analysis (YYYY-MM-DD or natural language like "last week", "3 months ago"). Default: 3 months.
-   `--until`, `-U` (type: `str`): End date for analysis (YYYY-MM-DD or natural language like "yesterday", "now"). Default: today.
-   `--author`, `-a` (type: `str`): Show detailed stats for a specific author (partial name/email match).
-   `--me`, `-m` (action: `store_true`): Show detailed stats for the current git user (uses git config user.name and user.email).
-   `--merges` (action: `store_true`): Only analyze commits that have been merged to the main branch (`origin/master` or `origin/main`).
-   `--path` (type: `str`, `nargs='*'`) : Include only changes to files within these paths (e.g., "src/frontend" "src/backend"). Can be specified multiple times.
-   `--exclude-path` (type: `str`, `nargs='*'`) : Exclude changes to files within these paths (e.g., "docs" "tests"). Can be specified multiple times.
-   `--default-period` (type: `str`): Default period to look back if `--since` or `--until` are not specified (e.g., "3 months", "1 year"). Default: "3 months".
-   `--pandas` (action: `store_true`): Use the pandas-based statistics engine (experimental).

## Development

To contribute to `git-scoreboard`, clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/git-scoreboard.git
cd git-scoreboard
pip install -e .n```

## Using the `git2df` Library

The `git2df` library provides a programmatic way to extract Git commit data and transform it into a Pandas DataFrame, making it easy to integrate Git analysis into other Python applications.

### Installation

`git2df` is part of the `git-scoreboard` project. If you have `git-scoreboard` installed, `git2df` is already available. If you only need the library, you can install it by installing `git-scoreboard`:

```bash
pip install git-scoreboard
```

### Basic Usage

To get a DataFrame of all commits in a repository:

```python
import pandas as pd
from git2df import get_commits_df

# Specify the path to your Git repository
repo_path = "/path/to/your/git/repo"

# Get all commits as a Pandas DataFrame
commits_df = get_commits_df(repo_path)

print(commits_df.head())
print(f"Total commits: {len(commits_df)}")
```

### Filtering Commits

You can filter commits by date range, author, or commit message using the `since`, `until`, `author`, and `grep` parameters:

```python
import pandas as pd
from git2df import get_commits_df

repo_path = "/path/to/your/git/repo"

# Get commits from the last month by a specific author, with a message containing "feature"
filtered_commits_df = get_commits_df(
    repo_path,
    since="1 month ago",
    until="now",
    author="John Doe",
    grep="feature"
)

print(filtered_commits_df.head())
print(f"Filtered commits: {len(filtered_commits_df)}")
```

### DataFrame Structure

The returned DataFrame includes the following columns, with one row per file change per commit:

-   `commit_hash`: SHA of the commit.
-   `parent_hash`: Optional; parent SHA.
-   `author_name`: Name of the commit author.
-   `author_email`: Email of the commit author.
-   `commit_date`: Timestamp of the commit (author date or committer date).
-   `file_paths`: Path of the file touched in this change.
-   `change_type`: Type of change (e.g., "A" for added, "M" for modified, "D" for deleted).
-   `additions`: Number of lines added in this specific file change.
-   `deletions`: Number of lines removed in this specific file change.
-   `commit_message`: Full commit message.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
