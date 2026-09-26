"""Structured logging setup with automated redaction of sensitive tokens and credentials."""

import logging
import sys


from backend.app.core.sanitizer import sanitize_for_logging


class SafeLogFormatter(logging.Formatter):
    """Custom formatter ensuring sensitive keywords (passwords, auth tokens, accounts) are masked."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return sanitize_for_logging(msg)


def setup_logging(debug: bool = False) -> None:
    """Initialize structured application logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    formatter = SafeLogFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Remove existing default handlers to prevent duplicate lines
    root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
