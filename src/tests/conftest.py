"""
Pytest configuration for OutboundOwl tests
"""

import sys
from pathlib import Path

# Add the src directory to Python path so tests can import from services
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path)) 