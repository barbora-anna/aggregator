"""Logging configuration."""

import logging

from app.config import settings


def init_logging() -> None:
    """Initialize logging configuration.

    Log level can be configured via LOG_LEVEL environment variable.
    Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    """
    log_format = logging.Formatter(
        fmt="{asctime} | {levelname} | {name} | {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(level=log_level, handlers=[console_handler], force=True)
