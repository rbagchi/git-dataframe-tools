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
        diagnose=debug,  # Show variables in traceback for debug mode
    )

    import logging

    # Configure standard logging to output to Loguru's sink
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelname

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    # Optionally, disable propagation to root logger if other libraries are still using it
    # logging.getLogger().handlers = [LoguruHandler()]
