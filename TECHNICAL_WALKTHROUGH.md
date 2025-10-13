# Technical Walkthrough of `git-dataframe-tools`

This document provides a technical overview of the `git-dataframe-tools` codebase, detailing its major components and their interactions, particularly focusing on the command-line interface (CLI) driven workflows.

## 1. Core Components

The codebase is structured around several key modules responsible for different aspects of Git data processing and analysis:

*   **`src/git_dataframe_tools/cli/`**: Contains the CLI entry points and related utilities.
    *   `git_df.py`: The main CLI program for generating a Git DataFrame.
    *   `scoreboard.py`: The CLI program for generating a Git author scoreboard.
    *   `common_args.py`: Defines common command-line arguments shared across CLI tools.
    *   `_display_utils.py`: Handles formatting and displaying output (e.g., tables, markdown).
    *   `_data_loader.py`: Manages loading and validating existing DataFrames.
*   **`src/git_dataframe_tools/config_models.py`**: Defines the `GitAnalysisConfig` dataclass, which encapsulates all configuration parameters for a Git analysis (e.g., date ranges, author filters, paths).
*   **`src/git_dataframe_tools/git_repo_info_provider.py`**: An abstract base class (`GitRepoInfoProvider`) defining an interface for retrieving Git repository information (e.g., current user, repository validity).
*   **`src/git_dataframe_tools/git_python_repo_info_provider.py`**: An implementation of `GitRepoInfoProvider` using the `GitPython` library.
*   **`src/git_dataframe_tools/git_stats_pandas.py`**: Contains the core logic for processing Git DataFrames using Pandas, primarily for calculating author statistics, ranks, and deciles.
*   **`src/git2df/`**: This package is responsible for the core functionality of converting Git log output into a structured DataFrame.
    *   `backends.py`: Implements `GitCliBackend`, which interacts with the underlying Git CLI to fetch raw log data.
    *   `dulwich/`: A subpackage containing components for a Dulwich-based backend (e.g., `repo_handler.py`, `commit_walker.py`, `diff_parser.py`).
    *   `git_parser/`: Handles the parsing of raw Git log output.
        *   `_commit_metadata_parser.py`: Parses individual commit metadata lines.
        *   `_file_stat_parser.py`: Parses file change statistics (additions, deletions, change type).
        *   `_chunk_processor.py`: Processes raw chunks of Git log output, combining metadata and file changes into `GitLogEntry` objects.
    *   `dataframe_builder.py`: Takes a list of `GitLogEntry` objects and constructs a Pandas DataFrame.

## 2. Major Code Flows (CLI-driven)

The primary interactions with the codebase are initiated via the command-line tools `git-df` and `git-scoreboard`. Both follow a similar high-level pattern:

### 2.1. General CLI Workflow

The general flow for any CLI command involves argument parsing, configuration setup, backend selection, data acquisition, and eventual processing/display.

```mermaid
sequenceDiagram
    participant User
    participant CLI_Program as CLI Program (git-df/git-scoreboard)
    participant common_args as common_args.py
    participant GitAnalysisConfig as GitAnalysisConfig (config_models.py)
    participant Backend as Git Backend (backends.py/dulwich)
    participant GitParser as Git Parser (git_parser/)
    participant DataFrameBuilder as DataFrame Builder (dataframe_builder.py)
    participant GitStatsPandas as GitStatsPandas (git_stats_pandas.py)
    participant DisplayUtils as Display Utilities (_display_utils.py)

    User->>CLI_Program: Executes command with arguments
    CLI_Program->>common_args: Parse CLI arguments
    common_args-->>CLI_Program: Parsed arguments
    CLI_Program->>GitAnalysisConfig: Create configuration object
    GitAnalysisConfig->>GitAnalysisConfig: Initialize with defaults & parsed args
    CLI_Program->>Backend: Select/Instantiate Git Backend (e.g., GitCliBackend)
    Backend->>Backend: Initialize with repo_path
    CLI_Program->>Backend: Request raw Git log data
    Backend->>GitParser: Raw Git log output
    GitParser->>GitParser: Parse raw output into GitLogEntry objects
    GitParser-->>CLI_Program: List of GitLogEntry objects
    CLI_Program->>DataFrameBuilder: Build Pandas DataFrame from GitLogEntry objects
    DataFrameBuilder-->>CLI_Program: Pandas DataFrame
    alt git-scoreboard specific
        CLI_Program->>GitStatsPandas: Calculate author statistics
        GitStatsPandas-->>CLI_Program: Author statistics
        CLI_Program->>DisplayUtils: Format and display results
    else git-df specific
        CLI_Program->>CLI_Program: Save or display DataFrame
    end
    DisplayUtils-->>User: Displayed output
    CLI_Program-->>User: Command completion
```

### 2.2. `git-df` Command Workflow

The `git-df` command focuses on extracting Git commit and file change data and presenting it as a Pandas DataFrame, which can then be saved or displayed.

```mermaid
sequenceDiagram
    participant User
    participant git_df as git-df CLI
    participant common_args as common_args.py
    participant GitAnalysisConfig as GitAnalysisConfig (config_models.py)
    participant GitCliBackend as GitCliBackend (backends.py)
    participant GitParser as Git Parser (git_parser/)
    participant DataFrameBuilder as DataFrame Builder (dataframe_builder.py)

    User->>git_df: git-df [options] [paths...]
    git_df->>common_args: Parse CLI arguments
    common_args-->>git_df: Parsed arguments
    git_df->>GitAnalysisConfig: Create configuration object
    GitAnalysisConfig->>GitAnalysisConfig: Apply date filters, author info
    git_df->>GitCliBackend: Instantiate with repo_path
    git_df->>GitCliBackend: get_raw_log_output(config)
    GitCliBackend->>GitCliBackend: Execute 'git show' commands for each commit
    GitCliBackend-->>git_df: Raw combined Git log output
    git_df->>GitParser: parse_git_log(raw_output)
    GitParser->>git_df: List of GitLogEntry objects
    git_df->>DataFrameBuilder: build_commits_df(GitLogEntry_list)
    DataFrameBuilder-->>git_df: Pandas DataFrame
    alt Output to file
        git_df->>git_df: Save DataFrame to Parquet/CSV
    else Display
        git_df->>_display_utils.py: Display DataFrame (e.g., print head)
    end
    git_df-->>User: Command completion / Output
```

### 2.3. `git-scoreboard` Command Workflow

The `git-scoreboard` command leverages the Git DataFrame to calculate and display author-centric statistics, including contributions, ranks, and deciles.

```mermaid
sequenceDiagram
    participant User
    participant scoreboard as git-scoreboard CLI
    participant common_args as common_args.py
    participant GitAnalysisConfig as GitAnalysisConfig (config_models.py)
    participant GitCliBackend as GitCliBackend (backends.py)
    participant GitParser as Git Parser (git_parser/)
    participant DataFrameBuilder as DataFrame Builder (dataframe_builder.py)
    participant GitStatsPandas as GitStatsPandas (git_stats_pandas.py)
    participant DisplayUtils as Display Utilities (_display_utils.py)
    participant DataLoader as Data Loader (_data_loader.py)

    User->>scoreboard: git-scoreboard [options] [paths...]
    scoreboard->>common_args: Parse CLI arguments
    common_args-->>scoreboard: Parsed arguments
    scoreboard->>GitAnalysisConfig: Create configuration object
    GitAnalysisConfig->>GitAnalysisConfig: Apply date filters, author info
    alt Load from existing DataFrame
        scoreboard->>DataLoader: Load DataFrame from file
        DataLoader-->>scoreboard: Pandas DataFrame
    else Generate new DataFrame
        scoreboard->>GitCliBackend: Instantiate with repo_path
        scoreboard->>GitCliBackend: get_raw_log_output(config)
        GitCliBackend-->>scoreboard: Raw combined Git log output
        scoreboard->>GitParser: parse_git_log(raw_output)
        GitParser-->>scoreboard: List of GitLogEntry objects
        scoreboard->>DataFrameBuilder: build_commits_df(GitLogEntry_list)
        DataFrameBuilder-->>scoreboard: Pandas DataFrame
    end
    scoreboard->>GitStatsPandas: parse_git_log(DataFrame)
    GitStatsPandas->>GitStatsPandas: Calculate author stats, ranks, deciles
    GitStatsPandas-->>scoreboard: List of author statistics (dict)
    scoreboard->>DisplayUtils: display_full_ranking(author_stats, config)
    DisplayUtils->>DisplayUtils: Format output (table/markdown)
    DisplayUtils-->>User: Displayed scoreboard
    scoreboard-->>User: Command completion
```
