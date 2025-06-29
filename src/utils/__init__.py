"""
Hedwig Utilities Package

This package contains shared utilities and helper functions used across the Hedwig services.
"""

# Import utilities as they are created
from .logging_utils import log, log_error, log_warning, log_info, log_debug, log_success
from .text_utils import TextProcessor
from .file_utils import FileUtils
from .error_utils import ErrorHandler, safe_operation, retry_operation_decorator
from .config_utils import ConfigUtils

__version__ = "1.0.0"
__author__ = "Hedwig Team"

# Export all utility classes and functions
__all__ = [
    "log",
    "log_error",
    "log_warning", 
    "log_info",
    "log_debug",
    "log_success",
    "TextProcessor",
    "FileUtils", 
    "ErrorHandler",
    "safe_operation",
    "retry_operation_decorator",
    "ConfigUtils",
] 