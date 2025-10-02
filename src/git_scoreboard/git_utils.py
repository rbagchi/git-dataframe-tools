import pandas as pd
import sys

from git_scoreboard.config_models import GitAnalysisConfig, print_error
from git2df import get_commits_df

def get_git_data_from_config(config: GitAnalysisConfig, repo_path: str = ".") -> pd.DataFrame:
    """Fetches git log data based on the configuration using git2df."""
    if not config._check_git_repo(repo_path): # Pass repo_path to _check_git_repo
        print_error("Error: Not in a git repository")
        sys.exit(1)

    try:
        df = get_commits_df(
            repo_path=repo_path,
            since=config.start_date.isoformat(),
            until=config.end_date.isoformat(),
            author=config.author_query,
            merged_only=config.merged_only,
            include_paths=config.include_paths,
            exclude_paths=config.exclude_paths
        )
        # print(f"DEBUG: Commits DataFrame from git2df:\n{df}") # Debug print
        return df
    except Exception as e:
        print_error(f"Error fetching git log data: {e}")
        sys.exit(1)
