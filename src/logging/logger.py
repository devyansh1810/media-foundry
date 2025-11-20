"""Structured logging configuration"""

import logging
import sys
from typing import Any

from src.config import get_settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data"""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "operation"):
            log_data["operation"] = record.operation
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration

        # Format as key=value pairs
        formatted_parts = [f"{k}={v!r}" for k, v in log_data.items()]
        return " ".join(formatted_parts)


def setup_logging() -> None:
    """Configure application logging"""
    settings = get_settings()

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    console_handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
