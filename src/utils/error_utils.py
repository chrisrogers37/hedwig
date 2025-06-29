"""
Error handling utilities for Hedwig.

This module provides standardized error handling patterns for file operations,
API calls, configuration operations, and general error formatting.
"""

from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps
from .logging_utils import log

T = TypeVar('T')


class ErrorHandler:
    """
    Utility class for standardized error handling across Hedwig services.
    
    Provides consistent error handling patterns for different types of operations
    with proper logging and error formatting.
    """
    
    @staticmethod
    def handle_file_operation(operation: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """
        Safely execute a file operation with standardized error handling.
        
        Args:
            operation: The file operation function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation, or None if it fails
        """
        try:
            result = operation(*args, **kwargs)
            return result
        except FileNotFoundError as e:
            log(f"ERROR: File not found: {e}", prefix="ErrorHandler")
            return None
        except PermissionError as e:
            log(f"ERROR: Permission denied: {e}", prefix="ErrorHandler")
            return None
        except UnicodeDecodeError as e:
            log(f"ERROR: Encoding error: {e}", prefix="ErrorHandler")
            return None
        except Exception as e:
            log(f"ERROR: Unexpected file operation error: {e}", prefix="ErrorHandler")
            return None
    
    @staticmethod
    def handle_api_operation(operation: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """
        Safely execute an API operation with standardized error handling.
        
        Args:
            operation: The API operation function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation, or None if it fails
        """
        try:
            result = operation(*args, **kwargs)
            return result
        except ConnectionError as e:
            log(f"ERROR: Connection error during API operation: {e}", prefix="ErrorHandler")
            return None
        except TimeoutError as e:
            log(f"ERROR: Timeout during API operation: {e}", prefix="ErrorHandler")
            return None
        except ValueError as e:
            log(f"ERROR: Invalid value in API operation: {e}", prefix="ErrorHandler")
            return None
        except Exception as e:
            log(f"ERROR: Unexpected API operation error: {e}", prefix="ErrorHandler")
            return None
    
    @staticmethod
    def handle_config_operation(operation: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """
        Safely execute a configuration operation with standardized error handling.
        
        Args:
            operation: The configuration operation function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation, or None if it fails
        """
        try:
            result = operation(*args, **kwargs)
            return result
        except KeyError as e:
            log(f"ERROR: Missing configuration key: {e}", prefix="ErrorHandler")
            return None
        except ValueError as e:
            log(f"ERROR: Invalid configuration value: {e}", prefix="ErrorHandler")
            return None
        except Exception as e:
            log(f"ERROR: Unexpected configuration operation error: {e}", prefix="ErrorHandler")
            return None
    
    @staticmethod
    def format_error_message(error: Exception, context: str = "") -> str:
        """
        Format an error message with context for consistent error reporting.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Formatted error message string
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        if context:
            return f"{context}: {error_type} - {error_msg}"
        else:
            return f"{error_type}: {error_msg}"
    
    @staticmethod
    def safe_execute(operation: Callable[..., T], 
                    error_context: str = "",
                    default_value: Optional[T] = None,
                    log_errors: bool = True) -> Optional[T]:
        """
        Generic safe execution wrapper for any operation.
        
        Args:
            operation: The operation function to execute
            error_context: Context for error logging
            default_value: Value to return if operation fails
            log_errors: Whether to log errors (default: True)
            
        Returns:
            Result of the operation, or default_value if it fails
        """
        try:
            result = operation()
            return result
        except Exception as e:
            if log_errors:
                formatted_error = ErrorHandler.format_error_message(e, error_context)
                log(f"ERROR: {formatted_error}", prefix="ErrorHandler")
            return default_value
    
    @staticmethod
    def retry_operation(operation: Callable[..., T],
                       max_retries: int = 3,
                       error_context: str = "",
                       retry_delay: float = 1.0) -> Optional[T]:
        """
        Execute an operation with retry logic for transient failures.
        
        Args:
            operation: The operation function to execute
            max_retries: Maximum number of retry attempts
            error_context: Context for error logging
            retry_delay: Delay between retries in seconds
            
        Returns:
            Result of the operation, or None if all retries fail
        """
        import time
        
        for attempt in range(max_retries + 1):
            try:
                result = operation()
                if attempt > 0:
                    log(f"Operation succeeded on attempt {attempt + 1}", prefix="ErrorHandler")
                return result
            except (ConnectionError, TimeoutError) as e:
                if attempt < max_retries:
                    log(f"Retry {attempt + 1}/{max_retries} after {error_context}: {e}", prefix="ErrorHandler")
                    time.sleep(retry_delay)
                else:
                    log(f"ERROR: Operation failed after {max_retries + 1} attempts: {error_context}: {e}", prefix="ErrorHandler")
                    return None
            except Exception as e:
                log(f"ERROR: Non-retryable error in {error_context}: {e}", prefix="ErrorHandler")
                return None
        
        return None


def safe_operation(error_context: str = "", default_value: Any = None):
    """
    Decorator for safe operation execution with error handling.
    
    Args:
        error_context: Context for error logging
        default_value: Value to return if operation fails
        
    Returns:
        Decorated function that handles errors safely
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            return ErrorHandler.safe_execute(
                lambda: func(*args, **kwargs),
                error_context=error_context,
                default_value=default_value
            )
        return wrapper
    return decorator


def retry_operation_decorator(max_retries: int = 3, error_context: str = "", retry_delay: float = 1.0):
    """
    Decorator for operation execution with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        error_context: Context for error logging
        retry_delay: Delay between retries in seconds
        
    Returns:
        Decorated function that retries on failure
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            return ErrorHandler.retry_operation(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                error_context=error_context,
                retry_delay=retry_delay
            )
        return wrapper
    return decorator 