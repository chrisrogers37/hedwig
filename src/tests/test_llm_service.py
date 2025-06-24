import pytest
from unittest.mock import patch, MagicMock
from services.llm_service import LLMService
from services.config_service import AppConfig
import os

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = AppConfig(load_env=False)
    config.set("OPENAI_API_KEY", "test-api-key")
    config.set("OPENAI_MODEL", "gpt-4")
    return config

@pytest.fixture
def llm_service(mock_config):
    """Create an LLM service instance for testing."""
    with patch('services.llm_service.openai.OpenAI') as mock_openai:
        # Mock the client and its chat.completions.create method
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )
        return LLMService(mock_config)

def test_llm_service_initialization(mock_config):
    """Test LLM service initialization with config."""
    with patch('services.llm_service.openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        service = LLMService(mock_config)
        assert service.config == mock_config

def test_llm_service_initialization_no_api_key():
    """Test LLM service initialization fails without API key."""
    # Save original value
    original_api_key = os.environ.get("OPENAI_API_KEY")
    
    # Unset for clean test
    os.environ.pop("OPENAI_API_KEY", None)
    
    try:
        config = AppConfig(load_env=False)
        # No API key set
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            LLMService(config)
    finally:
        # Restore original value
        if original_api_key:
            os.environ["OPENAI_API_KEY"] = original_api_key

def test_generate_response(llm_service):
    """Test generate_response method."""
    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Test response"
    llm_service.client.chat.completions.create.return_value = mock_response
    
    result = llm_service.generate_response("Test prompt")
    
    assert result == "Test response"
    llm_service.client.chat.completions.create.assert_called_once()

def test_generate_email_outreach(llm_service):
    """Test generate_email method for outreach emails."""
    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Generated outreach email"
    llm_service.client.chat.completions.create.return_value = mock_response
    
    context = {
        "your_name": "John Doe",
        "your_title": "Sales Manager",
        "company_name": "Test Corp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "value_propositions": [
            {"title": "Quality", "content": "High quality products"},
            {"title": "Price", "content": "Competitive pricing"}
        ],
        "call_to_action": "schedule a meeting"
    }
    
    result = llm_service.generate_email(context, "outreach")
    
    assert result == "Generated outreach email"
    llm_service.client.chat.completions.create.assert_called_once()

def test_generate_email_followup(llm_service):
    """Test generate_email method for followup emails."""
    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Generated followup email"
    llm_service.client.chat.completions.create.return_value = mock_response
    
    context = {
        "your_name": "John Doe",
        "your_title": "Sales Manager",
        "company_name": "Test Corp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "discussion_notes": "Discussed pricing and timeline",
        "pain_points": "Budget constraints",
        "next_steps": "Follow up next week"
    }
    
    result = llm_service.generate_email(context, "followup")
    
    assert result == "Generated followup email"
    llm_service.client.chat.completions.create.assert_called_once()

def test_generate_email_invalid_type(llm_service):
    """Test generate_email with invalid email type."""
    context = {"your_name": "John Doe"}
    
    with pytest.raises(ValueError, match="Unsupported email type"):
        llm_service.generate_email(context, "invalid_type")

def test_generate_response_api_error(llm_service):
    """Test generate_response handles API errors."""
    llm_service.client.chat.completions.create.side_effect = Exception("API Error")
    
    with pytest.raises(Exception, match="OpenAI API error: API Error"):
        llm_service.generate_response("Test prompt") 