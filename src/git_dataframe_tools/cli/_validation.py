import logging

logger = logging.getLogger(__name__)


def _validate_arguments(args):
    author_arg = getattr(args, "author", None)
    me_arg = getattr(args, "me", None)

    if author_arg and me_arg:
        logger.error("Error: Cannot use both --author and --me options together")
        return 1
    if (
        args.df_path and args.repo_path != "."
    ):  # If df_path is provided, repo_path should be default
        logger.error(
            "Error: Cannot use --df-path with a custom repo_path. The --df-path option replaces direct Git repository analysis."
        )
        return 1
    return 0
