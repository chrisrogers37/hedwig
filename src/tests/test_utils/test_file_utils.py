"""
Tests for FileUtils utility class.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from src.utils.file_utils import FileUtils


class TestFileUtils:
    """Test cases for FileUtils utility class."""
    
    def test_safe_read_file_success(self):
        """Test successful file reading."""
        test_content = "Test file content"
        test_path = Path("/tmp/test_file.txt")
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            result = FileUtils.safe_read_file(test_path)
        
        assert result == test_content
    
    def test_safe_read_file_not_found(self):
        """Test file reading when file doesn't exist."""
        test_path = Path("/nonexistent/file.txt")
        
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = FileUtils.safe_read_file(test_path)
        
        assert result is None
    
    def test_safe_read_file_permission_error(self):
        """Test file reading with permission error."""
        test_path = Path("/protected/file.txt")
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = FileUtils.safe_read_file(test_path)
        
        assert result is None
    
    def test_safe_read_file_encoding_error(self):
        """Test file reading with encoding error."""
        test_path = Path("/tmp/bad_encoding.txt")
        
        with patch('builtins.open', side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            result = FileUtils.safe_read_file(test_path)
        
        assert result is None
    
    def test_safe_read_file_unexpected_error(self):
        """Test file reading with unexpected error."""
        test_path = Path("/tmp/error.txt")
        
        with patch('builtins.open', side_effect=Exception("Unexpected error")):
            result = FileUtils.safe_read_file(test_path)
        
        assert result is None
    
    def test_safe_write_file_success(self):
        """Test successful file writing."""
        test_content = "Test content to write"
        test_path = Path("/tmp/test_write.txt")
        
        with patch('pathlib.Path.mkdir'), patch('builtins.open', mock_open()) as mock_file:
            result = FileUtils.safe_write_file(test_path, test_content)
        
        assert result is True
        mock_file.assert_called_once_with(test_path, 'w', encoding='utf-8')
    
    def test_safe_write_file_permission_error(self):
        """Test file writing with permission error."""
        test_content = "Test content"
        test_path = Path("/protected/write.txt")
        
        with patch('pathlib.Path.mkdir'), patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = FileUtils.safe_write_file(test_path, test_content)
        
        assert result is False
    
    def test_safe_write_file_unexpected_error(self):
        """Test file writing with unexpected error."""
        test_content = "Test content"
        test_path = Path("/tmp/error_write.txt")
        
        with patch('pathlib.Path.mkdir'), patch('builtins.open', side_effect=Exception("Unexpected error")):
            result = FileUtils.safe_write_file(test_path, test_content)
        
        assert result is False
    
    def test_find_files_by_extension_success(self):
        """Test finding files by extension."""
        test_dir = Path("/tmp/test_dir")
        test_files = [
            Path("/tmp/test_dir/file1.md"),
            Path("/tmp/test_dir/file2.md"),
            Path("/tmp/test_dir/subdir/file3.md")
        ]
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.rglob', return_value=test_files):
            result = FileUtils.find_files_by_extension(test_dir, '.md')
        
        assert result == test_files
    
    def test_find_files_by_extension_directory_not_exists(self):
        """Test finding files when directory doesn't exist."""
        test_dir = Path("/nonexistent/dir")
        
        with patch('pathlib.Path.exists', return_value=False):
            result = FileUtils.find_files_by_extension(test_dir, '.md')
        
        assert result == []
    
    def test_find_files_by_extension_not_directory(self):
        """Test finding files when path is not a directory."""
        test_dir = Path("/tmp/file.txt")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=False):
            result = FileUtils.find_files_by_extension(test_dir, '.md')
        
        assert result == []
    
    def test_find_files_by_extension_error(self):
        """Test finding files with unexpected error."""
        test_dir = Path("/tmp/test_dir")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.rglob', side_effect=Exception("Unexpected error")):
            result = FileUtils.find_files_by_extension(test_dir, '.md')
        
        assert result == []
    
    def test_parse_yaml_frontmatter_with_frontmatter(self):
        """Test parsing YAML frontmatter from content."""
        content = """---
tags: ["test", "example"]
use_case: "Test Case"
tone: "Professional"
industry: "Tech"
---

This is the actual content after the frontmatter."""
        
        metadata, text_content = FileUtils.parse_yaml_frontmatter(content)
        
        assert metadata == {
            "tags": ["test", "example"],
            "use_case": "Test Case",
            "tone": "Professional",
            "industry": "Tech"
        }
        assert text_content.strip() == "This is the actual content after the frontmatter."
    
    def test_parse_yaml_frontmatter_without_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "This is content without any frontmatter."
        
        metadata, text_content = FileUtils.parse_yaml_frontmatter(content)
        
        assert metadata == {}
        assert text_content == content
    
    def test_parse_yaml_frontmatter_invalid_yaml(self):
        """Test parsing frontmatter with invalid YAML."""
        content = """---
tags: ["unclosed", "list"
use_case: "Test Case"
---

This is the content."""
        
        metadata, text_content = FileUtils.parse_yaml_frontmatter(content)
        
        assert metadata == {}
        assert text_content.strip() == "This is the content."
    
    def test_parse_yaml_frontmatter_no_end_marker(self):
        """Test parsing frontmatter without end marker."""
        content = """---
tags: ["test"]
use_case: "Test Case"

This is the content."""
        
        metadata, text_content = FileUtils.parse_yaml_frontmatter(content)
        
        assert metadata == {}
        assert text_content == content
    
    def test_validate_file_exists_success(self):
        """Test file validation when file exists and is readable."""
        test_path = Path("/tmp/test_file.txt")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('builtins.open', mock_open()):
            result = FileUtils.validate_file_exists(test_path)
        
        assert result is True
    
    def test_validate_file_exists_not_found(self):
        """Test file validation when file doesn't exist."""
        test_path = Path("/nonexistent/file.txt")
        
        with patch('pathlib.Path.exists', return_value=False):
            result = FileUtils.validate_file_exists(test_path)
        
        assert result is False
    
    def test_validate_file_exists_not_file(self):
        """Test file validation when path is not a file."""
        test_path = Path("/tmp/directory")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=False):
            result = FileUtils.validate_file_exists(test_path)
        
        assert result is False
    
    def test_validate_file_exists_read_error(self):
        """Test file validation when file is not readable."""
        test_path = Path("/tmp/unreadable.txt")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = FileUtils.validate_file_exists(test_path)
        
        assert result is False
    
    def test_get_file_size_success(self):
        """Test getting file size successfully."""
        test_path = Path("/tmp/test_file.txt")
        expected_size = 1024
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = expected_size
            result = FileUtils.get_file_size(test_path)
        
        assert result == expected_size
    
    def test_get_file_size_error(self):
        """Test getting file size with error."""
        test_path = Path("/tmp/error_file.txt")
        
        with patch('pathlib.Path.stat', side_effect=Exception("Stat error")):
            result = FileUtils.get_file_size(test_path)
        
        assert result is None
    
    def test_create_directory_if_not_exists_success(self):
        """Test creating directory successfully."""
        test_dir = Path("/tmp/new_directory")
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            result = FileUtils.create_directory_if_not_exists(test_dir)
        
        assert result is True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_create_directory_if_not_exists_error(self):
        """Test creating directory with error."""
        test_dir = Path("/protected/new_directory")
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            result = FileUtils.create_directory_if_not_exists(test_dir)
        
        assert result is False
    
    def test_safe_read_file_with_custom_encoding(self):
        """Test file reading with custom encoding."""
        test_content = "Test content with special chars: éñ"
        test_path = Path("/tmp/test_file.txt")
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            result = FileUtils.safe_read_file(test_path, encoding='latin-1')
        
        assert result == test_content
    
    def test_safe_write_file_with_custom_encoding(self):
        """Test file writing with custom encoding."""
        test_content = "Test content with special chars: éñ"
        test_path = Path("/tmp/test_write.txt")
        
        with patch('pathlib.Path.mkdir'), patch('builtins.open', mock_open()) as mock_file:
            result = FileUtils.safe_write_file(test_path, test_content, encoding='latin-1')
        
        assert result is True
        mock_file.assert_called_once_with(test_path, 'w', encoding='latin-1')
    
    def test_parse_yaml_frontmatter_empty_content(self):
        """Test parsing YAML frontmatter with empty content."""
        content = ""
        
        metadata, text_content = FileUtils.parse_yaml_frontmatter(content)
        
        assert metadata == {}
        assert text_content == ""
    
    def test_parse_yaml_frontmatter_only_frontmatter(self):
        """Test parsing YAML frontmatter with only frontmatter."""
        content = """---
tags: ["test"]
use_case: "Test Case"
---"""
        
        metadata, text_content = FileUtils.parse_yaml_frontmatter(content)
        
        assert metadata == {"tags": ["test"], "use_case": "Test Case"}
        assert text_content.strip() == ""
    
    def test_find_files_by_extension_empty_result(self):
        """Test finding files by extension with no matches."""
        test_dir = Path("/tmp/empty_dir")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.rglob', return_value=[]):
            result = FileUtils.find_files_by_extension(test_dir, '.md')
        
        assert result == [] 