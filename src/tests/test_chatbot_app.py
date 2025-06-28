import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_chatbot_app_import():
    """Test that the chatbot app can be imported."""
    try:
        import app_chatbot
        assert hasattr(app_chatbot, 'main')
        assert hasattr(app_chatbot, 'initialize_services')
        assert hasattr(app_chatbot, 'render_configuration_sidebar')
        assert hasattr(app_chatbot, 'render_chat_interface')
    except ImportError as e:
        pytest.fail(f"Failed to import chatbot app: {e}")

def test_initialize_services_with_valid_config():
    """Test service initialization with valid configuration."""
    with patch('app_chatbot.AppConfig') as mock_config_class:
        mock_config = Mock()
        mock_config.validate.return_value = True
        mock_config.openai_api_key = "test-key"
        mock_config.openai_model = "gpt-4"
        mock_config.provider = "openai"
        mock_config_class.return_value = mock_config
        
        with patch('app_chatbot.LLMService') as mock_llm_class:
            with patch('app_chatbot.ChatHistoryManager') as mock_chat_class:
                with patch('app_chatbot.PromptBuilder') as mock_prompt_class:
                    with patch('app_chatbot.ScrollRetriever') as mock_scroll_class:
                        mock_llm = Mock()
                        mock_chat = Mock()
                        mock_prompt = Mock()
                        mock_scroll = Mock()
                        mock_llm_class.return_value = mock_llm
                        mock_chat_class.return_value = mock_chat
                        mock_prompt_class.return_value = mock_prompt
                        mock_scroll_class.return_value = mock_scroll
                        
                        import app_chatbot
                        config, llm_service, chat_history_manager, prompt_builder, scroll_retriever = app_chatbot.initialize_services()
                        
                        assert config is not None
                        assert llm_service is not None
                        assert chat_history_manager is not None
                        assert prompt_builder is not None
                        assert scroll_retriever is not None

def test_initialize_services_with_invalid_config():
    """Test service initialization with invalid configuration."""
    with patch('app_chatbot.AppConfig') as mock_config_class:
        mock_config = Mock()
        mock_config.validate.return_value = False
        mock_config.openai_api_key = "test-key"
        mock_config.openai_model = "gpt-4"
        mock_config.provider = "openai"
        mock_config_class.return_value = mock_config
        
        import app_chatbot
        config, llm_service, chat_history_manager, prompt_builder, scroll_retriever = app_chatbot.initialize_services()
        
        assert config is None
        assert llm_service is None
        assert chat_history_manager is None
        assert prompt_builder is None
        assert scroll_retriever is None 