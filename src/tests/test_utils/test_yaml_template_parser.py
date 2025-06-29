"""
Tests for YAML Template Parser utility.

Tests the YAMLTemplateParser class which handles parsing and extracting
components from YAML template files.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from utils.yaml_template_parser import YAMLTemplateParser


class TestYAMLTemplateParser:
    """Test YAMLTemplateParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = YAMLTemplateParser()
        
        # Sample valid YAML data
        self.valid_yaml_data = {
            'metadata': {
                'tags': ['test', 'email'],
                'use_case': 'Test Case',
                'tone': 'Professional',
                'industry': 'Tech',
                'notes': 'Test template notes'
            },
            'template': {
                'subject': 'Test Subject',
                'content': 'Test email content'
            },
            'guidance': {
                'tone': 'professional',
                'style': 'formal'
            }
        }
    
    def test_parse_template_valid(self):
        """Test parsing valid YAML template."""
        valid_yaml = """
metadata:
  tags: ["test", "email"]
  use_case: "Test Case"
  tone: "Professional"
  industry: "Tech"
template:
  subject: "Test Subject"
  content: "Test email content"
guidance:
  tone: "professional"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(valid_yaml)
            file_path = Path(f.name)
        
        try:
            result = self.parser.parse_template(file_path)
            assert 'metadata' in result
            assert 'template' in result
            assert 'guidance' in result
            assert result['metadata']['tags'] == ['test', 'email']
            assert result['template']['subject'] == 'Test Subject'
        finally:
            file_path.unlink()
    
    def test_parse_template_missing_sections(self):
        """Test parsing YAML with missing required sections."""
        invalid_yaml = """
metadata:
  tags: ["test"]
# Missing template section (required)
guidance:
  tone: "professional"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            file_path = Path(f.name)
        
        try:
            # Should not raise error due to ErrorHandler
            result = self.parser.parse_template(file_path)
            assert result is None  # ErrorHandler returns None on error
        finally:
            file_path.unlink()
    
    def test_parse_template_invalid_yaml(self):
        """Test parsing invalid YAML."""
        invalid_yaml = """
metadata:
  tags: ["test"
  # Missing closing bracket
template:
  content: "Test content"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            file_path = Path(f.name)
        
        try:
            result = self.parser.parse_template(file_path)
            assert result is None  # ErrorHandler returns None on error
        finally:
            file_path.unlink()
    
    def test_get_template_content_with_subject(self):
        """Test extracting template content with subject."""
        result = self.parser.get_template_content(self.valid_yaml_data)
        expected = "Subject: Test Subject\n\nTest email content"
        assert result == expected
    
    def test_get_template_content_without_subject(self):
        """Test extracting template content without subject."""
        yaml_data = {
            'template': {
                'content': 'Test email content'
            }
        }
        result = self.parser.get_template_content(yaml_data)
        assert result == 'Test email content'
    
    def test_get_template_content_empty(self):
        """Test extracting template content from empty template."""
        yaml_data = {'template': {}}
        result = self.parser.get_template_content(yaml_data)
        assert result == ''
    
    def test_get_metadata(self):
        """Test extracting metadata."""
        result = self.parser.get_metadata(self.valid_yaml_data)
        assert result['tags'] == ['test', 'email']
        assert result['use_case'] == 'Test Case'
        assert result['tone'] == 'Professional'
        assert result['industry'] == 'Tech'
    
    def test_get_metadata_empty(self):
        """Test extracting metadata from empty data."""
        yaml_data = {}
        result = self.parser.get_metadata(yaml_data)
        assert result == {}
    
    def test_get_guidance(self):
        """Test extracting guidance."""
        result = self.parser.get_guidance(self.valid_yaml_data)
        assert result['tone'] == 'professional'
        assert result['style'] == 'formal'
    
    def test_get_guidance_empty(self):
        """Test extracting guidance from empty data."""
        yaml_data = {}
        result = self.parser.get_guidance(yaml_data)
        assert result == {}
    
    def test_validate_template_valid(self):
        """Test validating valid template."""
        assert self.parser.validate_template(self.valid_yaml_data) is True
    
    def test_validate_template_missing_metadata(self):
        """Test validating template with missing metadata."""
        invalid_data = {
            'template': {
                'content': 'Test content'
            }
        }
        assert self.parser.validate_template(invalid_data) is False
    
    def test_validate_template_missing_template(self):
        """Test validating template with missing template section."""
        invalid_data = {
            'metadata': {
                'tags': ['test'],
                'use_case': 'Test',
                'tone': 'Professional',
                'industry': 'Tech'
            }
        }
        assert self.parser.validate_template(invalid_data) is False
    
    def test_validate_template_missing_required_fields(self):
        """Test validating template with missing required metadata fields."""
        invalid_data = {
            'metadata': {
                'tags': ['test'],
                'use_case': 'Test'
                # Missing tone and industry
            },
            'template': {
                'content': 'Test content'
            }
        }
        assert self.parser.validate_template(invalid_data) is False
    
    def test_validate_template_empty_content(self):
        """Test validating template with empty content."""
        invalid_data = {
            'metadata': {
                'tags': ['test'],
                'use_case': 'Test',
                'tone': 'Professional',
                'industry': 'Tech'
            },
            'template': {
                'content': ''  # Empty content
            }
        }
        assert self.parser.validate_template(invalid_data) is False
    
    def test_get_matching_content_full(self):
        """Test getting matching content with all components."""
        result = self.parser.get_matching_content(self.valid_yaml_data)
        
        # Should contain tags, notes, subject, and content
        assert 'test email' in result  # Tags
        assert 'Test template notes' in result  # Notes
        assert 'Subject: Test Subject' in result  # Subject
        assert 'Test email content' in result  # Content
    
    def test_get_matching_content_minimal(self):
        """Test getting matching content with minimal data."""
        minimal_data = {
            'metadata': {
                'tags': ['test']
            },
            'template': {
                'content': 'Test content'
            }
        }
        result = self.parser.get_matching_content(minimal_data)
        
        assert 'test' in result  # Tags
        assert 'Test content' in result  # Content
        assert 'Subject:' not in result  # No subject
    
    def test_get_matching_content_empty(self):
        """Test getting matching content from empty data."""
        empty_data = {}
        result = self.parser.get_matching_content(empty_data)
        assert result == ''
    
    def test_get_matching_content_only_tags(self):
        """Test getting matching content with only tags."""
        data = {
            'metadata': {
                'tags': ['tag1', 'tag2']
            },
            'template': {}
        }
        result = self.parser.get_matching_content(data)
        assert result == 'tag1 tag2'
    
    def test_get_matching_content_only_notes(self):
        """Test getting matching content with only notes."""
        data = {
            'metadata': {
                'notes': 'Important notes here'
            },
            'template': {}
        }
        result = self.parser.get_matching_content(data)
        assert result == 'Important notes here'
    
    def test_get_matching_content_only_subject(self):
        """Test getting matching content with only subject."""
        data = {
            'metadata': {},
            'template': {
                'subject': 'Important Subject'
            }
        }
        result = self.parser.get_matching_content(data)
        assert result == 'Subject: Important Subject'
    
    def test_get_matching_content_only_content(self):
        """Test getting matching content with only content."""
        data = {
            'metadata': {},
            'template': {
                'content': 'Important content here'
            }
        }
        result = self.parser.get_matching_content(data)
        assert result == 'Important content here' 