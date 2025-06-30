"""
Integration test to verify that the main app can import all dependencies.
This catches import errors that might not be caught by unit tests.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)


def test_app_imports():
    """Test that the main app can import all its dependencies."""
    try:
        # Test importing the main app
        from src.app_chatbot import (
            AppConfig,
            LLMService,
            PromptBuilder,
            ChatHistoryManager,
            MessageType,
            ScrollRetriever
        )
        print("✅ All app imports successful!")
    except ImportError as e:
        pytest.fail(f"❌ Import error: {e}")


def test_profile_manager_import():
    """Test that ProfileManager can be imported and used."""
    try:
        from src.services.profile_manager import ProfileManager
        # Test creating an instance
        profile_manager = ProfileManager()
        assert profile_manager is not None
        print("✅ ProfileManager import and instantiation successful!")
    except ImportError as e:
        pytest.fail(f"❌ ProfileManager import error: {e}")


def test_prompt_builder_with_profile_manager():
    """Test that PromptBuilder works with ProfileManager."""
    try:
        from src.services.prompt_builder import PromptBuilder
        from src.services.profile_manager import ProfileManager
        from src.services.chat_history_manager import ChatHistoryManager
        from unittest.mock import MagicMock
        
        # Create mock services
        mock_llm_service = MagicMock()
        chat_history_manager = ChatHistoryManager()
        profile_manager = ProfileManager()
        
        # Test PromptBuilder initialization with ProfileManager
        prompt_builder = PromptBuilder(
            mock_llm_service, 
            chat_history_manager, 
            profile_manager=profile_manager
        )
        
        assert prompt_builder.profile_manager is not None
        assert isinstance(prompt_builder.profile_manager, ProfileManager)
        print("✅ PromptBuilder with ProfileManager integration successful!")
        
    except Exception as e:
        pytest.fail(f"❌ PromptBuilder + ProfileManager integration error: {e}")


if __name__ == "__main__":
    # Run the tests
    test_app_imports()
    test_profile_manager_import()
    test_prompt_builder_with_profile_manager()
    print("🎉 All integration tests passed!")
def test_profile_management_function():
    """Test that the profile management function can be imported and works."""
    try:
        from src.app_chatbot import render_profile_management
        assert callable(render_profile_management)
        print("✅ Profile management function import successful!")
    except ImportError as e:
        pytest.fail(f"❌ Profile management function import error: {e}")
