"""
Pytest configuration for Hedwig tests.

This file ensures that the src/ directory is added to the Python path
so that imports like 'from utils.logging_utils import log' work correctly.
"""

import sys
from pathlib import Path

# Add src/ to Python path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path)) 