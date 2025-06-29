"""
Tests for logging_utils utility.
"""

import pytest
from unittest.mock import patch
import sys
from utils.logging_utils import log, log_error, log_warning, log_info, log_debug, log_success


class TestLoggingUtils:
    """Test cases for logging_utils module."""
    
    @patch('builtins.print')
    def test_log_default_prefix(self, mock_print):
        """Test log function with default prefix."""
        message = "Test message"
        log(message)
        
        mock_print.assert_called_once_with("[Hedwig] Test message")
    
    @patch('builtins.print')
    def test_log_custom_prefix(self, mock_print):
        """Test log function with custom prefix."""
        message = "Custom test message"
        prefix = "CustomPrefix"
        log(message, prefix)
        
        mock_print.assert_called_once_with("[CustomPrefix] Custom test message")
    
    @patch('builtins.print')
    def test_log_empty_message(self, mock_print):
        """Test log function with empty message."""
        message = ""
        log(message)
        
        mock_print.assert_called_once_with("[Hedwig] ")
    
    @patch('builtins.print')
    def test_log_special_characters(self, mock_print):
        """Test log function with special characters in message."""
        message = "Message with special chars: !@#$%^&*()"
        log(message)
        
        mock_print.assert_called_once_with("[Hedwig] Message with special chars: !@#$%^&*()")
    
    @patch('builtins.print')
    def test_log_multiline_message(self, mock_print):
        """Test log function with multiline message."""
        message = "Line 1\nLine 2\nLine 3"
        log(message)
        
        mock_print.assert_called_once_with("[Hedwig] Line 1\nLine 2\nLine 3")
    
    @patch('builtins.print')
    def test_log_numeric_message(self, mock_print):
        """Test log function with numeric message."""
        message = 123
        log(message)
        
        mock_print.assert_called_once_with("[Hedwig] 123")
    
    @patch('builtins.print')
    def test_log_empty_prefix(self, mock_print):
        """Test log function with empty prefix."""
        message = "Test message"
        prefix = ""
        log(message, prefix)
        
        mock_print.assert_called_once_with("[] Test message")
    
    @patch('builtins.print')
    def test_log_multiple_calls(self, mock_print):
        """Test multiple log calls."""
        log("First message")
        log("Second message", "TestPrefix")
        log("Third message")
        
        expected_calls = [
            (("[Hedwig] First message",),),
            (("[TestPrefix] Second message",),),
            (("[Hedwig] Third message",),)
        ]
        
        assert mock_print.call_args_list == expected_calls

    @patch('builtins.print')
    def test_log_error_default_prefix(self, mock_print):
        """Test log_error function with default prefix."""
        message = "Test error message"
        log_error(message)
        
        mock_print.assert_called_once_with("[Hedwig] ERROR: Test error message", file=sys.stderr)
    
    @patch('builtins.print')
    def test_log_error_with_exception(self, mock_print):
        """Test log_error function with exception."""
        message = "Test error message"
        exception = ValueError("Test exception")
        log_error(message, exception=exception)
        
        mock_print.assert_called_once_with("[Hedwig] ERROR: Test error message - Exception: ValueError: Test exception", file=sys.stderr)
    
    @patch('builtins.print')
    def test_log_warning_default_prefix(self, mock_print):
        """Test log_warning function with default prefix."""
        message = "Test warning message"
        log_warning(message)
        
        mock_print.assert_called_once_with("[Hedwig] WARNING: Test warning message")
    
    @patch('builtins.print')
    def test_log_info_default_prefix(self, mock_print):
        """Test log_info function with default prefix."""
        message = "Test info message"
        log_info(message)
        
        mock_print.assert_called_once_with("[Hedwig] INFO: Test info message")
    
    @patch('builtins.print')
    def test_log_debug_default_prefix(self, mock_print):
        """Test log_debug function with default prefix."""
        message = "Test debug message"
        log_debug(message)
        
        mock_print.assert_called_once_with("[Hedwig] DEBUG: Test debug message")
    
    @patch('builtins.print')
    def test_log_success_default_prefix(self, mock_print):
        """Test log_success function with default prefix."""
        message = "Test success message"
        log_success(message)
        
        mock_print.assert_called_once_with("[Hedwig] SUCCESS: Test success message")
    
    @patch('builtins.print')
    def test_log_error_custom_prefix(self, mock_print):
        """Test log_error function with custom prefix."""
        message = "Test error message"
        prefix = "CustomPrefix"
        log_error(message, prefix)
        
        mock_print.assert_called_once_with("[CustomPrefix] ERROR: Test error message", file=sys.stderr)
    
    @patch('builtins.print')
    def test_log_warning_custom_prefix(self, mock_print):
        """Test log_warning function with custom prefix."""
        message = "Test warning message"
        prefix = "CustomPrefix"
        log_warning(message, prefix)
        
        mock_print.assert_called_once_with("[CustomPrefix] WARNING: Test warning message")
    
    @patch('builtins.print')
    def test_log_info_custom_prefix(self, mock_print):
        """Test log_info function with custom prefix."""
        message = "Test info message"
        prefix = "CustomPrefix"
        log_info(message, prefix)
        
        mock_print.assert_called_once_with("[CustomPrefix] INFO: Test info message")
    
    @patch('builtins.print')
    def test_log_debug_custom_prefix(self, mock_print):
        """Test log_debug function with custom prefix."""
        message = "Test debug message"
        prefix = "CustomPrefix"
        log_debug(message, prefix)
        
        mock_print.assert_called_once_with("[CustomPrefix] DEBUG: Test debug message")
    
    @patch('builtins.print')
    def test_log_success_custom_prefix(self, mock_print):
        """Test log_success function with custom prefix."""
        message = "Test success message"
        prefix = "CustomPrefix"
        log_success(message, prefix)
        
        mock_print.assert_called_once_with("[CustomPrefix] SUCCESS: Test success message") 