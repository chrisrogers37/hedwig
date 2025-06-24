import pytest
from unittest.mock import Mock, patch
from services.prompt_builder import PromptBuilder, ConversationMessage, EmailContext
from services.llm_service import LLMService
from services.config_service import AppConfig

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = AppConfig(load_env=False)
    config.set("OPENAI_API_KEY", "test-api-key")
    config.set("OPENAI_MODEL", "gpt-4")
    return config

@pytest.fixture
def mock_llm_service(mock_config):
    """Create a mock LLM service for testing."""
    with patch('openai.ChatCompletion.create'):
        return LLMService(mock_config)

@pytest.fixture
def prompt_builder(mock_llm_service):
    """Create a fresh PromptBuilder instance for testing."""
    return PromptBuilder(mock_llm_service)

def test_prompt_builder_initialization(prompt_builder):
    """Test PromptBuilder initialization."""
    assert len(prompt_builder.conversation_history) == 0
    assert isinstance(prompt_builder.extracted_context, EmailContext)
    assert prompt_builder.llm_service is not None

def test_add_message(prompt_builder):
    """Test adding messages to conversation history."""
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = '{"your_name": "", "email_type": "outreach"}'
        
        prompt_builder.add_message("user", "Hello, I need help with an email")
        
        assert len(prompt_builder.conversation_history) == 1
        assert prompt_builder.conversation_history[0].role == "user"
        assert prompt_builder.conversation_history[0].content == "Hello, I need help with an email"

def test_extract_context_with_llm(prompt_builder):
    """Test LLM-based context extraction."""
    mock_response = '''{
        "your_name": "John Doe",
        "your_title": "Sales Manager",
        "company_name": "TechCorp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "email_type": "outreach",
        "value_propositions": [{"title": "Quality", "content": "High quality products"}],
        "call_to_action": "schedule a meeting"
    }'''
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_response
        
        prompt_builder.add_message("user", "My name is John Doe, I'm a Sales Manager at TechCorp")
        
        context = prompt_builder.get_context()
        assert context.your_name == "John Doe"
        assert context.your_title == "Sales Manager"
        assert context.company_name == "TechCorp"
        assert context.recipient_name == "Jane Smith"
        assert context.recipient_organization == "ABC Company"
        assert context.email_type == "outreach"
        assert len(context.value_propositions) == 1
        assert context.value_propositions[0]["title"] == "Quality"

def test_build_outreach_prompt(prompt_builder):
    """Test building outreach email prompt."""
    mock_response = '''{
        "your_name": "John Doe",
        "company_name": "TechCorp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "email_type": "outreach",
        "value_propositions": [{"title": "Competitive Pricing", "content": "Best prices in the market"}]
    }'''
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_response
        
        prompt_builder.add_message("user", "I need to write an outreach email")
        prompt = prompt_builder.build_email_prompt()
        
        assert "Initial Outreach" in prompt
        assert "John Doe" in prompt
        assert "TechCorp" in prompt
        assert "Jane Smith" in prompt
        assert "ABC Company" in prompt
        assert "Competitive Pricing" in prompt

def test_build_followup_prompt(prompt_builder):
    """Test building followup email prompt."""
    mock_response = '''{
        "your_name": "John Doe",
        "company_name": "TechCorp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "email_type": "followup",
        "discussion_notes": "pricing and timeline",
        "pain_points": "budget constraints",
        "next_steps": "follow up next week"
    }'''
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_response
        
        prompt_builder.add_message("user", "I need to follow up after our meeting")
        prompt = prompt_builder.build_email_prompt()
        
        assert "Follow-up" in prompt
        assert "John Doe" in prompt
        assert "TechCorp" in prompt
        assert "Jane Smith" in prompt
        assert "ABC Company" in prompt
        assert "pricing and timeline" in prompt.lower()
        assert "budget constraints" in prompt.lower()

def test_clear_conversation(prompt_builder):
    """Test clearing conversation history."""
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = '{"your_name": "Test"}'
        
        prompt_builder.add_message("user", "Test message")
        assert len(prompt_builder.conversation_history) == 1
        
        prompt_builder.clear_conversation()
        assert len(prompt_builder.conversation_history) == 0
        assert prompt_builder.extracted_context.your_name == ""

def test_context_defaults(prompt_builder):
    """Test that context has appropriate defaults."""
    context = prompt_builder.get_context()
    assert context.email_type == "outreach"
    assert context.tone == "professional"
    assert context.language == "English"
    assert context.value_propositions == []

def test_prompt_includes_tone_and_language(prompt_builder):
    """Test that generated prompts include tone and language settings."""
    mock_response = '{"email_type": "outreach"}'
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_response
        
        prompt_builder.add_message("user", "I need an email")
        prompt = prompt_builder.build_email_prompt()
        
        assert "Tone: professional" in prompt
        assert "Language: English" in prompt

def test_llm_extraction_fallback(prompt_builder):
    """Test that the system falls back gracefully if LLM extraction fails."""
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.side_effect = Exception("LLM API Error")
        
        prompt_builder.add_message("user", "Test message")
        
        # Should fall back to default context
        context = prompt_builder.get_context()
        assert context.your_name == ""
        assert context.email_type == "outreach"

def test_json_parsing_fallback(prompt_builder):
    """Test that the system handles invalid JSON responses gracefully."""
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = "Invalid JSON response"
        
        prompt_builder.add_message("user", "Test message")
        
        # Should fall back to default context
        context = prompt_builder.get_context()
        assert context.your_name == ""
        assert context.email_type == "outreach"

def test_llm_asks_question_when_info_missing(prompt_builder):
    """Test that LLM asks questions when critical information is missing."""
    mock_response = "What's your name?"
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_response
        
        prompt_builder.add_message("user", "I need to write an email")
        
        # Should have a question, not update context
        assert prompt_builder.has_question()
        assert prompt_builder.get_current_question() == "What's your name?"
        assert prompt_builder.extracted_context.your_name == ""  # Context not updated

def test_llm_clears_question_when_info_complete(prompt_builder):
    """Test that question is cleared when LLM gets complete information."""
    # First, LLM asks a question
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = "What's your name?"
        prompt_builder.add_message("user", "I need to write an email")
        assert prompt_builder.has_question()
    
    # Then, user provides complete information
    complete_response = '''{
        "your_name": "John Doe",
        "company_name": "TechCorp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "email_type": "outreach",
        "value_propositions": [{"title": "Quality", "content": "High quality"}]
    }'''
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = complete_response
        prompt_builder.add_message("user", "My name is John Doe from TechCorp")
        
        # Question should be cleared, context should be updated
        assert not prompt_builder.has_question()
        assert prompt_builder.get_current_question() is None
        assert prompt_builder.extracted_context.your_name == "John Doe"

def test_has_sufficient_context_outreach(prompt_builder):
    """Test context sufficiency check for outreach emails."""
    # Test insufficient context
    context = EmailContext(
        recipient_name="Jane Smith",
        recipient_organization="ABC Company",
        email_type="outreach"
        # Missing value propositions and call to action
    )
    prompt_builder.extracted_context = context
    assert not prompt_builder.has_sufficient_context()
    
    # Test sufficient context with value propositions
    context.value_propositions = [{"title": "Quality", "content": "High quality"}]
    prompt_builder.extracted_context = context
    assert prompt_builder.has_sufficient_context()
    
    # Test sufficient context with call to action
    context.value_propositions = []
    context.call_to_action = "schedule a meeting"
    prompt_builder.extracted_context = context
    assert prompt_builder.has_sufficient_context()

def test_has_sufficient_context_followup(prompt_builder):
    """Test context sufficiency check for followup emails."""
    # Test insufficient context
    context = EmailContext(
        recipient_name="Jane Smith",
        recipient_organization="ABC Company",
        email_type="followup"
        # Missing discussion notes and next steps
    )
    prompt_builder.extracted_context = context
    assert not prompt_builder.has_sufficient_context()
    
    # Test sufficient context with discussion notes
    context.discussion_notes = "pricing and timeline"
    prompt_builder.extracted_context = context
    assert prompt_builder.has_sufficient_context()
    
    # Test sufficient context with next steps
    context.discussion_notes = ""
    context.next_steps = "follow up next week"
    prompt_builder.extracted_context = context
    assert prompt_builder.has_sufficient_context()

def test_has_sufficient_context_missing_recipient(prompt_builder):
    """Test that missing recipient info makes context insufficient."""
    context = EmailContext(
        your_name="John Doe",
        company_name="TechCorp",
        email_type="outreach",
        value_propositions=[{"title": "Quality", "content": "High quality"}]
        # Missing recipient info
    )
    prompt_builder.extracted_context = context
    assert not prompt_builder.has_sufficient_context()

def test_clear_conversation_clears_question(prompt_builder):
    """Test that clearing conversation also clears any current question."""
    # Set up a question
    prompt_builder.current_question = "What's your name?"
    assert prompt_builder.has_question()
    
    # Clear conversation
    prompt_builder.clear_conversation()
    assert not prompt_builder.has_question()
    assert prompt_builder.get_current_question() is None

class MockLLMService:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    def generate_response(self, prompt, max_tokens=1200):
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp

def test_prompt_builder_conversational(monkeypatch):
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