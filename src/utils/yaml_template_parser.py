"""
YAML Template Parser

This module provides utilities for parsing YAML template files and extracting
metadata, template content, and guidance components.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .error_utils import ErrorHandler
from .logging_utils import log


class YAMLTemplateParser:
    """Parse YAML template files and extract components."""
    
    def parse_template(self, file_path: Path) -> Dict[str, Any]:
        """Parse YAML template file and return structured data."""
        def parse_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Validate required sections
            required_sections = ['metadata', 'template']
            for section in required_sections:
                if section not in data:
                    raise ValueError(f"Missing required section: {section}")
            
            return data
        
        return ErrorHandler.handle_file_operation(parse_file)
    
    def get_template_content(self, yaml_data: Dict) -> str:
        """Extract template content for embedding generation."""
        template = yaml_data.get('template', {})
        subject = template.get('subject', '')
        content = template.get('content', '')
        
        if subject:
            return f"Subject: {subject}\n\n{content}"
        return content
    
    def get_metadata(self, yaml_data: Dict) -> Dict[str, Any]:
        """Extract metadata for filtering and organization."""
        return yaml_data.get('metadata', {})
    
    def get_guidance(self, yaml_data: Dict) -> Dict[str, Any]:
        """Extract writing guidance for prompts."""
        return yaml_data.get('guidance', {})
    
    def validate_template(self, yaml_data: Dict) -> bool:
        """Validate template structure and required fields."""
        # Check required sections
        if 'metadata' not in yaml_data or 'template' not in yaml_data:
            return False
        
        # Check required metadata fields
        metadata = yaml_data['metadata']
        required_fields = ['tags', 'use_case', 'tone', 'industry']
        if not all(field in metadata for field in required_fields):
            return False
        
        # Check template content
        template = yaml_data['template']
        if 'content' not in template or not template['content'].strip():
            return False
        
        return True
    
    def get_matching_content(self, yaml_data: Dict) -> str:
        """Get content used for matching (tags, notes, and template content)."""
        metadata = yaml_data.get('metadata', {})
        template = yaml_data.get('template', {})
        
        # Extract tags and notes for matching
        tags = metadata.get('tags', [])
        notes = metadata.get('notes', '')
        
        # Extract template content
        subject = template.get('subject', '')
        content = template.get('content', '')
        
        # Combine for matching
        matching_parts = []
        
        # Add tags as space-separated string
        if tags:
            matching_parts.append(' '.join(tags))
        
        # Add notes
        if notes:
            matching_parts.append(notes)
        
        # Add template content
        if subject:
            matching_parts.append(f"Subject: {subject}")
        if content:
            matching_parts.append(content)
        
        return '\n\n'.join(matching_parts) 