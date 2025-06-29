"""
Tests for text_utils utility.
"""

import pytest
from utils.text_utils import TextProcessor

class TestTextProcessor:
    def test_normalize_whitespace(self):
        assert TextProcessor.normalize_whitespace('  Hello   world!  ') == 'Hello world!'
        assert TextProcessor.normalize_whitespace('\nHello\tworld\n') == 'Hello world'
        assert TextProcessor.normalize_whitespace('NoExtraSpaces') == 'NoExtraSpaces'

    def test_clean_special_chars(self):
        assert TextProcessor.clean_special_chars('Hello, world!') == 'Hello world'
        assert TextProcessor.clean_special_chars('A-B_C.D!', keep_chars='-') == 'A-B_CD'
        assert TextProcessor.clean_special_chars('123@#$', keep_chars='@') == '123@'
        assert TextProcessor.clean_special_chars('NoSpecials') == 'NoSpecials'

    def test_preprocess_text(self):
        assert TextProcessor.preprocess_text('  Hello,   world!  ') == 'hello world'
        assert TextProcessor.preprocess_text('\nA-B_C.D!\t', ) == 'a-b_cd'
        assert TextProcessor.preprocess_text('NoSpecials') == 'nospecials' 