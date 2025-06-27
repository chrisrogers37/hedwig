"""
Tests for logging_utils service.
"""

import pytest
from unittest.mock import patch
from services.logging_utils import log


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