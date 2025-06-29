"""
Logging utilities for Hedwig.

This module provides standardized logging functions for consistent logging across the application.
"""

import sys
from typing import Optional


def log(msg: str, prefix: str = "Hedwig") -> None:
    """Log a message with the specified prefix."""
    print(f"[{prefix}] {msg}")


def log_error(msg: str, prefix: str = "Hedwig", exception: Optional[Exception] = None) -> None:
    """Log an error message with optional exception details."""
    error_msg = f"ERROR: {msg}"
    if exception:
        error_msg += f" - Exception: {type(exception).__name__}: {str(exception)}"
    print(f"[{prefix}] {error_msg}", file=sys.stderr)


def log_warning(msg: str, prefix: str = "Hedwig") -> None:
    """Log a warning message."""
    print(f"[{prefix}] WARNING: {msg}")


def log_info(msg: str, prefix: str = "Hedwig") -> None:
    """Log an info message."""
    print(f"[{prefix}] INFO: {msg}")


def log_debug(msg: str, prefix: str = "Hedwig") -> None:
    """Log a debug message."""
    print(f"[{prefix}] DEBUG: {msg}")


def log_success(msg: str, prefix: str = "Hedwig") -> None:
    """Log a success message."""
    print(f"[{prefix}] SUCCESS: {msg}") 