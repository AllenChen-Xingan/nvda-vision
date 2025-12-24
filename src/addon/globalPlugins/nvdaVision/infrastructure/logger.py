"""Logging configuration for NVDA Vision plugin.

This module sets up Loguru-based logging with security considerations
to comply with real.md constraint 2 (no sensitive data in logs).
"""

import sys
import re
from pathlib import Path
from typing import Optional
from loguru import logger as loguru_logger

# Remove default handler
loguru_logger.remove()

# Global logger instance
logger = loguru_logger


def setup_logger(
    log_dir: Path,
    level: str = "INFO",
    retention_days: int = 7,
    max_file_size_mb: int = 10
) -> None:
    """Configure Loguru logger for NVDA Vision plugin.

    Satisfies real.md constraint 2: No sensitive data in logs.

    Args:
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        retention_days: How many days to keep old logs
        max_file_size_mb: Max size of each log file before rotation
    """
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler (colored, human-readable)
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
        filter=sanitize_log_record,  # Apply security filter
    )

    # File handler (structured, machine-readable)
    log_file = log_dir / "nvda_vision_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        rotation=f"{max_file_size_mb} MB",  # Rotate at size limit
        retention=f"{retention_days} days",  # Keep for N days
        compression="zip",  # Compress old logs
        level=level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        enqueue=True,  # Thread-safe
        backtrace=True,
        diagnose=True,
        filter=sanitize_log_record,  # Apply security filter
    )

    logger.info(
        f"Logger initialized: level={level}, log_dir={log_dir}, "
        f"retention={retention_days}d, max_size={max_file_size_mb}MB"
    )


def sanitize_log_record(record: dict) -> bool:
    """Filter to remove sensitive data from logs.

    Ensures compliance with real.md constraint 2: no API keys in logs.

    Args:
        record: Loguru log record dictionary

    Returns:
        True to include record, False to drop it
    """
    message = record["message"]

    # Mask API keys (starts with sk-, mk-, ak- etc.)
    message = re.sub(
        r'\b([sma]k-[a-zA-Z0-9]{4})[a-zA-Z0-9]+([a-zA-Z0-9]{4})\b',
        r'\1...\2',
        message
    )

    # Mask long base64 strings (potential encrypted keys)
    message = re.sub(
        r'\b([A-Za-z0-9+/]{8})[A-Za-z0-9+/]{32,}([A-Za-z0-9+/=]{8})\b',
        r'\1...\2',
        message
    )

    # Mask potential passwords
    message = re.sub(
        r'(password|pwd|pass)["\s:=]+["\']?([^\s"\',]{2})[^\s"\',]*([^\s"\',]{2})',
        r'\1=\2...\3',
        message,
        flags=re.IGNORECASE
    )

    # Mask potential tokens
    message = re.sub(
        r'(token|auth|bearer)["\s:=]+["\']?([^\s"\',]{4})[^\s"\',]*([^\s"\',]{4})',
        r'\1=\2...\3',
        message,
        flags=re.IGNORECASE
    )

    record["message"] = message
    return True


def get_logger(name: Optional[str] = None):
    """Get logger instance with optional name binding.

    Args:
        name: Optional logger name for context

    Returns:
        Configured logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger


# Convenience functions for common logging patterns

def log_model_event(event: str, model_name: str, **kwargs):
    """Log model-related event with context.

    Args:
        event: Event description
        model_name: Model name
        **kwargs: Additional context
    """
    logger.info(
        f"Model event: {event}",
        model=model_name,
        **kwargs
    )


def log_recognition_event(event: str, screenshot_hash: str, **kwargs):
    """Log recognition-related event.

    Args:
        event: Event description
        screenshot_hash: Screenshot hash (first 8 chars only for privacy)
        **kwargs: Additional context
    """
    # Only log first 8 characters of hash for privacy
    logger.info(
        f"Recognition event: {event}",
        screenshot_hash=screenshot_hash[:8] if screenshot_hash else "none",
        **kwargs
    )


def log_cache_event(event: str, **kwargs):
    """Log cache-related event.

    Args:
        event: Event description
        **kwargs: Additional context
    """
    logger.debug(f"Cache event: {event}", **kwargs)


def log_error_with_context(error: Exception, context: str, **kwargs):
    """Log error with additional context.

    Args:
        error: Exception instance
        context: Context description
        **kwargs: Additional context
    """
    logger.exception(
        f"Error in {context}: {type(error).__name__}: {str(error)}",
        **kwargs
    )


# Export logger instance and functions
__all__ = [
    "logger",
    "setup_logger",
    "get_logger",
    "log_model_event",
    "log_recognition_event",
    "log_cache_event",
    "log_error_with_context",
]
