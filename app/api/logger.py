import logging
import sys
from typing import NoReturn


def get_logger(name: str) -> logging.Logger:
    """Create and return a logger with the specified name."""
    return logging.getLogger(name)


def log_error(logger: logging.Logger, message: str) -> NoReturn:
    """Log an exception with an informative error message, and exit the app."""
    logger.error(message)
    sys.exit(1)
