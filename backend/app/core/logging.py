"""
Sentinel Backend — Structured Logging Configuration
Uses structlog for JSON-formatted, request-ID-aware logs.
NEVER log secrets, API keys, or webhook signatures.
"""
import logging
import sys
import structlog
from app.core.config import get_settings


def configure_logging() -> None:
    """Configure structlog for structured, JSON-formatted logging."""
    settings = get_settings()

    log_level = logging.DEBUG if settings.app_debug else logging.INFO

    # Standard library logging config
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.app_debug:
        # Human-readable in development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # JSON in production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "sentinel"):
    """Get a structured logger instance."""
    return structlog.get_logger(name)
