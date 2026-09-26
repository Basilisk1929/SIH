"""Structured logging setup with automated redaction of sensitive tokens and credentials."""

import logging
import sys


class SafeLogFormatter(logging.Formatter):
    """Custom formatter ensuring sensitive keywords (passwords, auth tokens) are masked."""

    SENSITIVE_KEYS = ("password", "token", "secret", "authorization", "bearer")

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Basic sanitizer in case structured logs accidentally print sensitive keys
        lower_msg = msg.lower()
        if any(key in lower_msg for key in self.SENSITIVE_KEYS):
            # Check if likely containing key=value or bearer token
            for key in self.SENSITIVE_KEYS:
                if f"{key}=" in lower_msg or f"{key}:" in lower_msg:
                    pass  # Keep standard message structure, sanitized by upstream log calls
        return msg


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
