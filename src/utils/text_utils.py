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

    @staticmethod
    def extract_sentences(text: str) -> list:
        """Split text into sentences using simple punctuation rules."""
        # This is a simple sentence splitter; for more advanced, use nltk or spacy
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s for s in sentences if s]

    @staticmethod
    def find_phrase_context(text: str, phrase: str, context_chars: int = 50) -> str:
        """Find the context around a phrase in text (returns phrase with surrounding chars)."""
        idx = text.lower().find(phrase.lower())
        if idx == -1:
            return ""
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(phrase) + context_chars)
        return text[start:end]

    @staticmethod
    def calculate_word_count(text: str) -> int:
        """Count the number of words in the text."""
        return len(text.strip().split())

    @staticmethod
    def detect_placeholders(text: str) -> list:
        """Detect template placeholders in the text (e.g., {name}, <company>, etc.)."""
        # Match {placeholder}, <placeholder>, or [[placeholder]]
        pattern = r'(\{[^}]+\}|<[^>]+>|\[\[[^\]]+\]\])'
        return re.findall(pattern, text) 