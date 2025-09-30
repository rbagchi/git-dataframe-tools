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
    git-scoreboard --start 2025-06-01
    ```

-   **Scenario: Analyze contributions from "last week" to "yesterday".**
    ```bash
    git-scoreboard --start "last week" --end "yesterday"
    ```

-   **Scenario: Analyze contributions from "3 months ago" to "now".**
    ```bash
    git-scoreboard --start "3 months ago" --end "now"
    ```

-   **Scenario: Review team output for a period ending on a specific date (e.g., last 3 months before August 31st, 2025).**
    ```bash
    git-scoreboard --end 2025-08-31
    ```

-   **Scenario: Get the full picture for a specific project phase or quarter (e.g., between June 1st and August 31st, 2025).**
    ```bash
    git-scoreboard --start 2025-06-01 --end 2025-08-31
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
    git-scoreboard --me --start 2025-06-01
    ```

-   **Scenario: Focus only on production-ready code – analyze commits that have been merged to the main branch.**
    ```bash
    git-scoreboard --merged-only
    ```

-   **Scenario: See *your* merged contributions only – prove your impact on the main codebase.**
    ```bash
    git-scoreboard --me --merged-only
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

### Arguments

-   `--start`, `-s` (type: `str`): Start date for analysis (YYYY-MM-DD or natural language like "last week", "3 months ago"). Default: 3 months ago.
-   `--end`, `-e` (type: `str`): End date for analysis (YYYY-MM-DD or natural language like "yesterday", "now"). Default: today.
-   `--author`, `-a` (type: `str`): Show detailed stats for a specific author (partial name/email match).
-   `--me`, `-m` (action: `store_true`): Show detailed stats for the current git user (equivalent to `--author` with your git config).
-   `--merged-only` (action: `store_true`): Only analyze commits that have been merged to the main branch (`origin/master` or `origin/main`).
-   `--path` (type: `str`, `nargs='*'`) : Include only changes to files within these paths (e.g., "src/frontend" "src/backend"). Can be specified multiple times.
-   `--exclude-path` (type: `str`, `nargs='*'`) : Exclude changes to files within these paths (e.g., "docs" "tests"). Can be specified multiple times.
-   `--default-period` (type: `str`): Default period to look back if --start is not specified (e.g., "3 months", "1 year"). Default: "3 months".

## Development

To contribute to `git-scoreboard`, clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/git-scoreboard.git
cd git-scoreboard
pip install -e .n```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
