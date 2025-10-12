import os
import pyarrow.parquet as pq
import logging
from typing import Optional

from git_dataframe_tools.config_models import GitAnalysisConfig
from git_dataframe_tools.git_repo_info_provider import GitRepoInfoProvider

logger = logging.getLogger(__name__)

EXPECTED_DATA_VERSION = "1.0"  # Expected major version of the DataFrame schema


def _load_dataframe(args, config: GitAnalysisConfig):
    git_log_data = None
    if args.df_path:
        if not os.path.exists(args.df_path):
            logger.error(f"DataFrame file not found at '{args.df_path}'")
            return None, 1
        logger.info(f"Loading commit data from '{args.df_path}'...")
        try:
            table = pq.read_table(args.df_path)
            metadata = table.schema.metadata

            loaded_data_version = None
            if b"data_version" in metadata:
                loaded_data_version = metadata[b"data_version"].decode()

            if loaded_data_version and loaded_data_version != EXPECTED_DATA_VERSION:
                message = f"DataFrame version mismatch. Expected '{EXPECTED_DATA_VERSION}', but found '{loaded_data_version}'."
                if not args.force_version_mismatch:
                    logger.error(
                        f"{message} Aborting. Use --force-version-mismatch to proceed anyway."
                    )
                    return None, 1
                else:
                    logger.warning(
                        f"{message} Proceeding due to --force-version-mismatch."
                    )
            elif not loaded_data_version:
                message = "No 'data_version' metadata found in the DataFrame file."
                if not args.force_version_mismatch:
                    logger.error(
                        f"{message} Aborting. Use --force-version-mismatch to proceed anyway."
                    )
                    return None, 1
                else:
                    logger.warning(
                        f"{message} Proceeding due to --force-version-mismatch."
                    )

            git_log_data = table.to_pandas()
        except Exception as e:
            logger.error(f"Error loading DataFrame from '{args.df_path}': {e}")
            return None, 1
    return git_log_data, 0


def _gather_git_data(
    args,
    config: GitAnalysisConfig,
    repo_info_provider: Optional[GitRepoInfoProvider] = None,
):
    from git2df import get_commits_df

    logger.info("Gathering commit data directly from Git...")
    try:
        # The check for local repo is now handled by GitAnalysisConfig's repo_info_provider
        # if not args.remote_url:
        #     if not check_git_repo(args.repo_path):
        #         logger.error("Not in a git repository")
        #         return None, 1

        git_log_data = get_commits_df(
            repo_path=(
                args.repo_path if not args.remote_url else "."
            ),  # Pass repo_path only if local
            remote_url=args.remote_url,
            remote_branch=args.remote_branch,
            since=config.start_date.isoformat() if config.start_date else None,
            until=config.end_date.isoformat() if config.end_date else None,
            author=config.author_query,
            merged_only=config.merged_only,
            include_paths=config.include_paths,
            exclude_paths=config.exclude_paths,
        )
        return git_log_data, 0
    except Exception as e:
        logger.error(f"Error fetching git log data: {e}", exc_info=True)
        return None, 1
