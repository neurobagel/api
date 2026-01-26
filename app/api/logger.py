import logging
from typing import NoReturn, Type


def get_logger(name: str) -> logging.Logger:
    """Create and return a logger with the specified name."""
    return logging.getLogger(name)


def log_and_raise_error(
    logger: logging.Logger, exception_type: Type[Exception], message: str
) -> NoReturn:
    """
    Log an error with an informative message,
    then raise the specified exception type with the same message,
    exiting the app.
    """
    logger.error(message)
    raise exception_type(message)
