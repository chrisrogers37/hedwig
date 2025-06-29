"""
Text processing utilities for Hedwig.

This module provides standardized text preprocessing functions for use across the application.
"""

import re

class TextProcessor:
    @staticmethod
    def preprocess_text(text: str) -> str:
        """Preprocess text by lowercasing, normalizing whitespace, and cleaning special characters (preserve hyphens)."""
        text = text.lower()
        text = TextProcessor.normalize_whitespace(text)
        text = TextProcessor.clean_special_chars(text, keep_chars="-")
        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Replace multiple whitespace characters with a single space and strip leading/trailing whitespace."""
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def clean_special_chars(text: str, keep_chars: str = "") -> str:
        """Remove special characters from text, except those in keep_chars."""
        if keep_chars:
            pattern = rf'[^\w\s{re.escape(keep_chars)}]'
        else:
            pattern = r'[^\w\s]'
        return re.sub(pattern, '', text) 