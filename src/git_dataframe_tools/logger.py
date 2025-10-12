import sys
from loguru import logger

def setup_logging(debug: bool = False, verbose: bool = False):
    """
    Sets up logging for the application using Loguru.

    Args:
        debug: If True, set log level to DEBUG.
        verbose: If True, set log level to INFO.
    """
    # Remove default handler to prevent duplicate messages
    logger.remove()

    level = "WARNING"
    if verbose:
        level = "INFO"
    if debug:
        level = "DEBUG"

    # Add a sink for console output
    logger.add(
        sys.stderr,  # Use stderr for logs by default
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        diagnose=debug, # Show variables in traceback for debug mode
    )

    # Optionally, disable propagation to root logger if other libraries are still using it
    # logging.getLogger().handlers = [LoguruHandler()]