"""
File I/O utilities for Hedwig.

This module provides standardized file operations including safe file reading,
writing, YAML frontmatter parsing, and file discovery utilities.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from .logging_utils import log


class FileUtils:
    """
    Utility class for standardized file operations across Hedwig services.
    
    Provides safe file reading, writing, YAML parsing, and file discovery
    with consistent error handling and logging.
    """
    
    @staticmethod
    def safe_read_file(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
        """
        Safely read a file with error handling and logging.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string, or None if reading fails
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            log(f"Successfully read file: {file_path}")
            return content
        except FileNotFoundError:
            log(f"ERROR: File not found: {file_path}", prefix="FileUtils")
            return None
        except PermissionError:
            log(f"ERROR: Permission denied reading file: {file_path}", prefix="FileUtils")
            return None
        except UnicodeDecodeError as e:
            log(f"ERROR: Encoding error reading file {file_path}: {e}", prefix="FileUtils")
            return None
        except Exception as e:
            log(f"ERROR: Unexpected error reading file {file_path}: {e}", prefix="FileUtils")
            return None
    
    @staticmethod
    def safe_write_file(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
        """
        Safely write content to a file with error handling and logging.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if writing succeeds, False otherwise
        """
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            log(f"Successfully wrote file: {file_path}")
            return True
        except PermissionError:
            log(f"ERROR: Permission denied writing file: {file_path}", prefix="FileUtils")
            return False
        except Exception as e:
            log(f"ERROR: Unexpected error writing file {file_path}: {e}", prefix="FileUtils")
            return False
    
    @staticmethod
    def find_files_by_extension(directory: Path, extension: str) -> List[Path]:
        """
        Find all files with a specific extension in a directory.
        
        Args:
            directory: Directory to search in
            extension: File extension to search for (e.g., '.md', '.json')
            
        Returns:
            List of file paths matching the extension
        """
        try:
            if not directory.exists():
                log(f"WARNING: Directory does not exist: {directory}", prefix="FileUtils")
                return []
            
            if not directory.is_dir():
                log(f"WARNING: Path is not a directory: {directory}", prefix="FileUtils")
                return []
            
            files = list(directory.rglob(f"*{extension}"))
            log(f"Found {len(files)} files with extension '{extension}' in {directory}", prefix="FileUtils")
            return files
        except Exception as e:
            log(f"ERROR: Unexpected error searching directory {directory}: {e}", prefix="FileUtils")
            return []
    
    @staticmethod
    def parse_yaml_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Raw markdown content with optional YAML frontmatter
            
        Returns:
            Tuple of (metadata, content) where metadata is a dict and content is the remaining text
        """
        lines = content.split('\n')
        
        # Check if content starts with frontmatter
        if not lines or not lines[0].strip().startswith('---'):
            return {}, content
        
        # Find frontmatter boundaries
        start_idx = 0
        end_idx = None
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_idx = i
                break
        
        if end_idx is None:
            log("WARNING: Frontmatter start marker found but no end marker", prefix="FileUtils")
            return {}, content
        
        # Extract and parse frontmatter
        frontmatter_lines = lines[1:end_idx]
        frontmatter_text = '\n'.join(frontmatter_lines)
        
        try:
            metadata = yaml.safe_load(frontmatter_text) or {}
            log(f"Successfully parsed YAML frontmatter with {len(metadata)} fields", prefix="FileUtils")
        except yaml.YAMLError as e:
            log(f"ERROR parsing YAML frontmatter: {e}", prefix="FileUtils")
            metadata = {}
        
        # Extract content after frontmatter
        content_lines = lines[end_idx + 1:]
        content = '\n'.join(content_lines)
        
        return metadata, content
    
    @staticmethod
    def validate_file_exists(file_path: Path) -> bool:
        """
        Validate that a file exists and is readable.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file exists and is readable, False otherwise
        """
        try:
            if not file_path.exists():
                log(f"File does not exist: {file_path}", prefix="FileUtils")
                return False
            
            if not file_path.is_file():
                log(f"Path is not a file: {file_path}", prefix="FileUtils")
                return False
            
            # Test if file is readable
            with open(file_path, 'r') as f:
                f.read(1)  # Read one character to test readability
            
            return True
        except Exception as e:
            log(f"ERROR validating file {file_path}: {e}", prefix="FileUtils")
            return False
    
    @staticmethod
    def get_file_size(file_path: Path) -> Optional[int]:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, or None if unable to determine
        """
        try:
            return file_path.stat().st_size
        except Exception as e:
            log(f"ERROR getting file size for {file_path}: {e}", prefix="FileUtils")
            return None
    
    @staticmethod
    def create_directory_if_not_exists(directory: Path) -> bool:
        """
        Create a directory if it doesn't exist.
        
        Args:
            directory: Path to the directory to create
            
        Returns:
            True if directory exists or was created successfully, False otherwise
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            log(f"Directory ready: {directory}", prefix="FileUtils")
            return True
        except Exception as e:
            log(f"ERROR creating directory {directory}: {e}", prefix="FileUtils")
            return False 