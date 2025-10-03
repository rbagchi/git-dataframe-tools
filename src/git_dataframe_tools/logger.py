import logging
import sys


def setup_logging(debug: bool = False, verbose: bool = False):
    """
    Sets up logging for the application.

    Args:
        debug: If True, set log level to DEBUG.
        verbose: If True, set log level to INFO.
    """
    level = logging.WARNING
    if verbose:
        level = logging.INFO
    if debug:
        level = logging.DEBUG

    # Configure the root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Set specific log levels for potentially chatty libraries if needed
    # logging.getLogger('git2df').setLevel(level)
    # logging.getLogger('git_dataframe_tools').setLevel(level)
