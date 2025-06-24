import pytest
from unittest.mock import patch, Mock
import sys
import os
from services.prompt_builder import PromptBuilder

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
        mock_config_class.return_value = mock_config
        
        with patch('app_chatbot.LLMService') as mock_llm_class:
            with patch('app_chatbot.PromptBuilder') as mock_prompt_class:
                mock_llm = Mock()
                mock_prompt = Mock()
                mock_llm_class.return_value = mock_llm
                mock_prompt_class.return_value = mock_prompt
                
                import app_chatbot
                config, llm_service, prompt_builder = app_chatbot.initialize_services()
                
                assert config is not None
                assert llm_service is not None
                assert prompt_builder is not None

def test_initialize_services_with_invalid_config():
    """Test service initialization with invalid configuration."""
    with patch('app_chatbot.AppConfig') as mock_config_class:
        mock_config = Mock()
        mock_config.validate.return_value = False
        mock_config_class.return_value = mock_config
        
        import app_chatbot
        config, llm_service, prompt_builder = app_chatbot.initialize_services()
        
        assert config is None
        assert llm_service is None
        assert prompt_builder is None

class MockLLMService:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    def generate_response(self, prompt, max_tokens=1200):
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp

def test_conversational_flow(monkeypatch):
    # Simulate a conversation with explicit info, missing info, and final email
    responses = [
        "Could you tell me the recipient's name?",
        "Could you tell me your company name?",
        "Subject: Welcome to OutboundOwl\nHi Chris, ...\nBest, John",
    ]
    pb = PromptBuilder()
    pb.llm_service = MockLLMService(responses)
    pb.add_message("user", "I want to send an outreach email.")
    assert pb.has_question()
    assert "recipient" in pb.get_current_question().lower()
    pb.add_message("user", "The recipient is Chris.")
    assert pb.has_question()
    assert "company" in pb.get_current_question().lower()
    pb.add_message("user", "My company is OutboundOwl.")
    assert pb.has_generated_email()
    email = pb.get_generated_email()
    assert email.startswith("Subject:")
    assert "Chris" in email
    assert "OutboundOwl" in email 