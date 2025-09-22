"""Main entry point for fr_env_resolver CLI."""

import logging
import os

from .parse import parse_args
from .resolve import resolve
from .execute import execute


def setup_logging(log_level: str) -> None:
    """Set up logging configuration.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    fr_env_logger = logging.getLogger("fr_env_resolver")
    fr_env_logger.setLevel(numeric_level)

    if not fr_env_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(numeric_level)
        formatter = logging.Formatter("%(name)s:%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        fr_env_logger.addHandler(handler)

    if numeric_level <= logging.DEBUG:
        fr_config_logger = logging.getLogger("fr_config")
        fr_config_logger.setLevel(logging.DEBUG)
        if not fr_config_logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(name)s:%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            fr_config_logger.addHandler(handler)


def main() -> None:
    """Main entry point for fr_env_resolver."""
    args = parse_args()
    setup_logging(args.log_level)
    execution_context = resolve(args)
    execute(args, execution_context)
