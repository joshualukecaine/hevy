"""Logging configuration for the Hevy CLI."""

import logging
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


def setup_logging(
    level: LogLevel = "INFO",
    verbose: bool = False,
) -> None:
    """Configure logging for the CLI.

    Args:
        level: Logging level
        verbose: If True, use DEBUG level
    """
    if verbose:
        level = "DEBUG"

    # Simple formatter for console
    console_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Set hevy logger specifically
    hevy_logger = logging.getLogger("hevy")
    hevy_logger.setLevel(level)

    # Reduce noise from requests library
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
