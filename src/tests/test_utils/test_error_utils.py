"""
Tests for ErrorHandler utility class.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from src.utils.error_utils import ErrorHandler, safe_operation, retry_operation_decorator


class TestErrorHandler:
    """Test cases for ErrorHandler utility class."""
    
    def test_handle_file_operation_success(self):
        """Test successful file operation handling."""
        def mock_file_operation(content):
            return f"Processed: {content}"
        
        result = ErrorHandler.handle_file_operation(mock_file_operation, "test content")
        assert result == "Processed: test content"
    
    def test_handle_file_operation_file_not_found(self):
        """Test file operation with FileNotFoundError."""
        def mock_file_operation():
            raise FileNotFoundError("File not found")
        
        result = ErrorHandler.handle_file_operation(mock_file_operation)
        assert result is None
    
    def test_handle_file_operation_permission_error(self):
        """Test file operation with PermissionError."""
        def mock_file_operation():
            raise PermissionError("Permission denied")
        
        result = ErrorHandler.handle_file_operation(mock_file_operation)
        assert result is None
    
    def test_handle_file_operation_unicode_error(self):
        """Test file operation with UnicodeDecodeError."""
        def mock_file_operation():
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        
        result = ErrorHandler.handle_file_operation(mock_file_operation)
        assert result is None
    
    def test_handle_file_operation_unexpected_error(self):
        """Test file operation with unexpected error."""
        def mock_file_operation():
            raise ValueError("Unexpected error")
        
        result = ErrorHandler.handle_file_operation(mock_file_operation)
        assert result is None
    
    def test_handle_api_operation_success(self):
        """Test successful API operation handling."""
        def mock_api_operation(data):
            return f"API response: {data}"
        
        result = ErrorHandler.handle_api_operation(mock_api_operation, "test data")
        assert result == "API response: test data"
    
    def test_handle_api_operation_connection_error(self):
        """Test API operation with ConnectionError."""
        def mock_api_operation():
            raise ConnectionError("Connection failed")
        
        result = ErrorHandler.handle_api_operation(mock_api_operation)
        assert result is None
    
    def test_handle_api_operation_timeout_error(self):
        """Test API operation with TimeoutError."""
        def mock_api_operation():
            raise TimeoutError("Request timeout")
        
        result = ErrorHandler.handle_api_operation(mock_api_operation)
        assert result is None
    
    def test_handle_api_operation_value_error(self):
        """Test API operation with ValueError."""
        def mock_api_operation():
            raise ValueError("Invalid value")
        
        result = ErrorHandler.handle_api_operation(mock_api_operation)
        assert result is None
    
    def test_handle_api_operation_unexpected_error(self):
        """Test API operation with unexpected error."""
        def mock_api_operation():
            raise RuntimeError("Unexpected API error")
        
        result = ErrorHandler.handle_api_operation(mock_api_operation)
        assert result is None
    
    def test_handle_config_operation_success(self):
        """Test successful configuration operation handling."""
        def mock_config_operation(key):
            return f"Config value for {key}"
        
        result = ErrorHandler.handle_config_operation(mock_config_operation, "test_key")
        assert result == "Config value for test_key"
    
    def test_handle_config_operation_key_error(self):
        """Test configuration operation with KeyError."""
        def mock_config_operation():
            raise KeyError("Missing key")
        
        result = ErrorHandler.handle_config_operation(mock_config_operation)
        assert result is None
    
    def test_handle_config_operation_value_error(self):
        """Test configuration operation with ValueError."""
        def mock_config_operation():
            raise ValueError("Invalid config value")
        
        result = ErrorHandler.handle_config_operation(mock_config_operation)
        assert result is None
    
    def test_handle_config_operation_unexpected_error(self):
        """Test configuration operation with unexpected error."""
        def mock_config_operation():
            raise TypeError("Unexpected config error")
        
        result = ErrorHandler.handle_config_operation(mock_config_operation)
        assert result is None
    
    def test_format_error_message_with_context(self):
        """Test error message formatting with context."""
        error = ValueError("Invalid input")
        formatted = ErrorHandler.format_error_message(error, "API call")
        assert formatted == "API call: ValueError - Invalid input"
    
    def test_format_error_message_without_context(self):
        """Test error message formatting without context."""
        error = FileNotFoundError("File not found")
        formatted = ErrorHandler.format_error_message(error)
        assert formatted == "FileNotFoundError: File not found"
    
    def test_safe_execute_success(self):
        """Test safe execution with successful operation."""
        def mock_operation():
            return "success"
        
        result = ErrorHandler.safe_execute(mock_operation, "test context")
        assert result == "success"
    
    def test_safe_execute_with_error(self):
        """Test safe execution with error."""
        def mock_operation():
            raise ValueError("Test error")
        
        result = ErrorHandler.safe_execute(mock_operation, "test context")
        assert result is None
    
    def test_safe_execute_with_default_value(self):
        """Test safe execution with custom default value."""
        def mock_operation():
            raise RuntimeError("Test error")
        
        result = ErrorHandler.safe_execute(mock_operation, "test context", default_value="default")
        assert result == "default"
    
    def test_safe_execute_no_logging(self):
        """Test safe execution without error logging."""
        def mock_operation():
            raise ValueError("Test error")
        
        with patch('src.utils.error_utils.log') as mock_log:
            result = ErrorHandler.safe_execute(mock_operation, "test context", log_errors=False)
            assert result is None
            mock_log.assert_not_called()
    
    def test_retry_operation_success_first_try(self):
        """Test retry operation that succeeds on first try."""
        def mock_operation():
            return "success"
        
        result = ErrorHandler.retry_operation(mock_operation, max_retries=3, error_context="test")
        assert result == "success"
    
    def test_retry_operation_success_after_retries(self):
        """Test retry operation that succeeds after retries."""
        call_count = 0
        
        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = ErrorHandler.retry_operation(mock_operation, max_retries=3, error_context="test")
        
        assert result == "success"
        assert call_count == 3
    
    def test_retry_operation_all_retries_fail(self):
        """Test retry operation that fails all retries."""
        def mock_operation():
            raise ConnectionError("Connection failed")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = ErrorHandler.retry_operation(mock_operation, max_retries=2, error_context="test")
        
        assert result is None
    
    def test_retry_operation_non_retryable_error(self):
        """Test retry operation with non-retryable error."""
        def mock_operation():
            raise ValueError("Non-retryable error")
        
        result = ErrorHandler.retry_operation(mock_operation, max_retries=3, error_context="test")
        assert result is None
    
    def test_retry_operation_zero_retries(self):
        """Test retry operation with zero retries."""
        def mock_operation():
            raise ConnectionError("Connection failed")
        
        result = ErrorHandler.retry_operation(mock_operation, max_retries=0, error_context="test")
        assert result is None


class TestSafeOperationDecorator:
    """Test cases for safe_operation decorator."""
    
    def test_safe_operation_decorator_success(self):
        """Test safe_operation decorator with successful function."""
        @safe_operation("test context")
        def mock_function():
            return "success"
        
        result = mock_function()
        assert result == "success"
    
    def test_safe_operation_decorator_with_error(self):
        """Test safe_operation decorator with error."""
        @safe_operation("test context")
        def mock_function():
            raise ValueError("Test error")
        
        result = mock_function()
        assert result is None
    
    def test_safe_operation_decorator_with_default_value(self):
        """Test safe_operation decorator with custom default value."""
        @safe_operation("test context", default_value="default")
        def mock_function():
            raise RuntimeError("Test error")
        
        result = mock_function()
        assert result == "default"
    
    def test_safe_operation_decorator_with_arguments(self):
        """Test safe_operation decorator with function arguments."""
        @safe_operation("test context")
        def mock_function(x, y):
            return x + y
        
        result = mock_function(2, 3)
        assert result == 5
    
    def test_safe_operation_decorator_with_keyword_arguments(self):
        """Test safe_operation decorator with keyword arguments."""
        @safe_operation("test context")
        def mock_function(x, y=0):
            return x + y
        
        result = mock_function(5, y=3)
        assert result == 8


class TestRetryOperationDecorator:
    """Test cases for retry_operation_decorator."""
    
    def test_retry_operation_decorator_success_first_try(self):
        """Test retry_operation_decorator that succeeds on first try."""
        @retry_operation_decorator(max_retries=3, error_context="test")
        def mock_function():
            return "success"
        
        result = mock_function()
        assert result == "success"
    
    def test_retry_operation_decorator_success_after_retries(self):
        """Test retry_operation_decorator that succeeds after retries."""
        call_count = 0
        
        @retry_operation_decorator(max_retries=3, error_context="test")
        def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = mock_function()
        
        assert result == "success"
        assert call_count == 3
    
    def test_retry_operation_decorator_all_retries_fail(self):
        """Test retry_operation_decorator that fails all retries."""
        @retry_operation_decorator(max_retries=2, error_context="test")
        def mock_function():
            raise ConnectionError("Connection failed")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = mock_function()
        
        assert result is None
    
    def test_retry_operation_decorator_with_arguments(self):
        """Test retry_operation_decorator with function arguments."""
        @retry_operation_decorator(max_retries=2, error_context="test")
        def mock_function(x, y):
            return x + y
        
        result = mock_function(2, 3)
        assert result == 5
    
    def test_retry_operation_decorator_custom_retry_delay(self):
        """Test retry_operation_decorator with custom retry delay."""
        call_count = 0
        
        @retry_operation_decorator(max_retries=2, error_context="test", retry_delay=0.5)
        def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "success"
        
        with patch('time.sleep') as mock_sleep:  # Mock sleep to verify delay
            result = mock_function()
        
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once_with(0.5) 