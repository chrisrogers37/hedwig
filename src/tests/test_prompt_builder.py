import pytest
from unittest.mock import Mock, patch
from services.prompt_builder import PromptBuilder, Profile
from services.llm_service import LLMService
from services.config_service import AppConfig
from services.chat_history_manager import ChatHistoryManager, MessageType

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = AppConfig(load_env=False)
    config.set("OPENAI_API_KEY", "test-api-key")
    config.set("OPENAI_MODEL", "gpt-4")
    config.set("DEFAULT_TONE", "professional")
    config.set("DEFAULT_LANGUAGE", "English")
    return config

@pytest.fixture
def mock_llm_service(mock_config):
    """Create a mock LLM service for testing."""
    with patch('openai.ChatCompletion.create'):
        return LLMService(mock_config)

@pytest.fixture
def chat_history_manager():
    """Create a fresh ChatHistoryManager instance for testing."""
    return ChatHistoryManager()

@pytest.fixture
def prompt_builder(mock_llm_service, chat_history_manager, mock_config):
    """Create a fresh PromptBuilder instance for testing."""
    return PromptBuilder(mock_llm_service, chat_history_manager, config=mock_config)

def test_prompt_builder_initialization(prompt_builder, chat_history_manager):
    """Test PromptBuilder initialization."""
    assert prompt_builder.llm_service is not None
    assert prompt_builder.chat_history_manager is chat_history_manager
    assert isinstance(prompt_builder.profile, Profile)

def test_build_outreach_prompt_tone_instructions(prompt_builder):
    context = {
        "your_name": "John Doe",
        "your_title": "Sales Manager",
        "company_name": "Test Corp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "tone": "casual",
        "language": "English",
        "value_propositions": [
            {"title": "Quality", "content": "High quality products"}
        ],
        "call_to_action": "schedule a meeting"
    }
    prompt = prompt_builder.build_outreach_prompt(context)
    assert "Tone: casual" in prompt
    assert "Use simple, easy-to-understand language." in prompt
    assert "Key Value Propositions" in prompt
    assert "schedule a meeting" in prompt

def test_build_followup_prompt_tone_instructions(prompt_builder):
    context = {
        "your_name": "John Doe",
        "your_title": "Sales Manager",
        "company_name": "Test Corp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "tone": "formal",
        "language": "English",
        "discussion_notes": "Discussed pricing and timeline",
        "pain_points": "Budget constraints",
        "next_steps": "Follow up next week"
    }
    prompt = prompt_builder.build_followup_prompt(context)
    assert "Tone: formal" in prompt
    assert "Use highly structured, polite, and respectful language." in prompt
    assert "Discussed pricing and timeline" in prompt
    assert "Budget constraints" in prompt
    assert "Follow up next week" in prompt

def test_build_outreach_prompt_default_tone(prompt_builder):
    context = {
        "your_name": "John Doe",
        "your_title": "Sales Manager",
        "company_name": "Test Corp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        # No tone provided, should use config default
    }
    prompt = prompt_builder.build_outreach_prompt(context)
    assert "Tone: professional" in prompt
    assert "Use clear, concise, and formal business language." in prompt

def test_build_followup_prompt_friendly_tone(prompt_builder):
    context = {
        "your_name": "John Doe",
        "your_title": "Sales Manager",
        "company_name": "Test Corp",
        "recipient_name": "Jane Smith",
        "recipient_organization": "ABC Company",
        "tone": "friendly"
    }
    prompt = prompt_builder.build_followup_prompt(context)
    assert "Tone: friendly" in prompt
    assert "Write in a warm, approachable, and personable manner." in prompt

def test_build_llm_prompt_with_empty_history(prompt_builder):
    """Test building prompt with empty conversation history."""
    prompt = prompt_builder.build_llm_prompt()
    
    assert "expert assistant for writing outreach emails for any use case" in prompt
    assert "[No user request provided]" in prompt
    assert "[No profile info provided]" in prompt

def test_build_llm_prompt_with_conversation_history(prompt_builder, chat_history_manager):
    """Test building prompt with conversation history."""
    # Add some messages to the conversation
    chat_history_manager.add_message("I need help writing an outreach email", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("Here's a draft email for you...")
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "expert assistant for writing outreach emails for any use case" in prompt
    assert "Make it more professional" in prompt  # Latest feedback should be included
    assert "I need help writing an outreach email" not in prompt  # Only latest user message is used

def test_build_llm_prompt_with_profile(prompt_builder):
    """Test building prompt with user profile information."""
    # Update profile
    prompt_builder.update_profile(
        your_name="John Doe",
        your_title="Sales Manager",
        company_name="TechCorp"
    )
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "John Doe" in prompt
    assert "Sales Manager" in prompt
    assert "TechCorp" in prompt

def test_build_llm_prompt_latest_user_message_only(prompt_builder, chat_history_manager):
    """Test that only the latest user message is used in the prompt."""
    # Add multiple user messages
    chat_history_manager.add_message("First request", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("First draft")
    chat_history_manager.add_message("Second request", MessageType.INITIAL_PROMPT)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "Second request" in prompt  # Latest user message
    assert "First request" not in prompt  # Earlier user message should not be included

def test_build_llm_prompt_with_feedback(prompt_builder, chat_history_manager):
    """Test building prompt with feedback in the conversation."""
    # Add conversation with feedback
    chat_history_manager.add_message("Write me an outreach email", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("Here's a draft...")
    chat_history_manager.add_message("Make it more concise", MessageType.FEEDBACK)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "Make it more concise" in prompt  # Latest feedback should be included
    assert "Most recent feedback from user:" in prompt

def test_build_llm_prompt_natural_tone(prompt_builder, mock_config):
    """Test building prompt with natural tone."""
    # Update config to use natural tone
    mock_config.set("DEFAULT_TONE", "natural")
    prompt_builder.config = mock_config
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "Tone: natural" in prompt
    assert "Use simple language and intentionally try to not sound AI-written" in prompt

def test_generate_draft(prompt_builder, chat_history_manager):
    """Test generating a draft using the full conversation context."""
    # Add user message to history
    chat_history_manager.add_message("I need an outreach email for a potential client", MessageType.INITIAL_PROMPT)
    
    # Mock LLM response
    mock_draft = "Dear [Recipient Name],\n\nI hope this email finds you well..."
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_draft
        
        draft = prompt_builder.generate_draft()
        
        assert draft == mock_draft
        assert prompt_builder.get_draft_email() == mock_draft
        
        # Verify the draft was added to chat history
        messages = chat_history_manager.get_messages_by_type(MessageType.DRAFT)
        assert len(messages) == 1
        assert messages[0].content == mock_draft

def test_generate_draft_with_feedback(prompt_builder, chat_history_manager):
    """Test generating a draft with feedback in the conversation history."""
    # Add conversation with feedback
    chat_history_manager.add_message("Write me an outreach email", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("Here's a draft...")
    chat_history_manager.add_message("Make it more concise", MessageType.FEEDBACK)
    
    # Mock LLM response
    mock_revised_draft = "Dear [Name],\n\nI wanted to reach out..."
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_revised_draft
        
        draft = prompt_builder.generate_draft()
        
        assert draft == mock_revised_draft
        
        # Verify the new draft was added to chat history
        drafts = chat_history_manager.get_messages_by_type(MessageType.DRAFT)
        assert len(drafts) == 2  # Original draft + new draft

def test_update_profile(prompt_builder):
    """Test updating user profile."""
    prompt_builder.update_profile(
        your_name="Jane Smith",
        your_title="Marketing Director",
        company_name="Innovation Inc"
    )
    
    assert prompt_builder.profile.your_name == "Jane Smith"
    assert prompt_builder.profile.your_title == "Marketing Director"
    assert prompt_builder.profile.company_name == "Innovation Inc"

def test_get_draft_email(prompt_builder):
    """Test getting the current draft email."""
    # Initially no draft
    assert prompt_builder.get_draft_email() is None
    
    # Set a draft
    prompt_builder.draft_email = "Test draft email"
    assert prompt_builder.get_draft_email() == "Test draft email"

def test_prompt_includes_conversation_summary(prompt_builder, chat_history_manager):
    """Test that prompt focuses on latest user message and feedback, not full conversation summary."""
    # Add messages and create a summary
    chat_history_manager.add_message("Initial request", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("First draft")
    chat_history_manager.add_message("Latest feedback", MessageType.FEEDBACK)
    
    # Create a summary (this is no longer used in the prompt)
    chat_history_manager.summary = "Previous conversation about outreach email with feedback"
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Current implementation focuses on latest user message and feedback, not summary
    assert "Latest feedback" in prompt
    assert "Most recent feedback from user:" in prompt
    # Summary is no longer included in the prompt
    assert "Previous conversation about outreach email with feedback" not in prompt

def test_prompt_with_max_messages_limit(prompt_builder, chat_history_manager):
    """Test that prompt focuses on latest user message, not full conversation context."""
    # Add many messages
    for i in range(10):
        chat_history_manager.add_message(f"Message {i}", MessageType.INITIAL_PROMPT)
        chat_history_manager.add_draft(f"Draft {i}")
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Current implementation only uses the latest user message
    assert "Message 9" in prompt  # Latest message
    assert "Message 0" not in prompt  # Earlier messages not included
    # Full conversation context is no longer included
    assert "Conversation so far:" not in prompt

def test_error_handling_in_generate_draft(prompt_builder, chat_history_manager):
    """Test error handling when LLM service fails."""
    chat_history_manager.add_message("Test message", MessageType.INITIAL_PROMPT)
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.side_effect = Exception("LLM API Error")
        
        with pytest.raises(Exception, match="LLM API Error"):
            prompt_builder.generate_draft()

def test_profile_defaults(prompt_builder):
    """Test that profile has appropriate defaults."""
    assert prompt_builder.profile.your_name == ""
    assert prompt_builder.profile.your_title == ""
    assert prompt_builder.profile.company_name == ""

def test_custom_profile_initialization():
    """Test PromptBuilder initialization with custom profile."""
    mock_llm_service = Mock()
    chat_history_manager = ChatHistoryManager()
    
    custom_profile = Profile(
        your_name="Custom Name",
        your_title="Custom Title",
        company_name="Custom Company"
    )
    
    prompt_builder = PromptBuilder(mock_llm_service, chat_history_manager, custom_profile)
    
    assert prompt_builder.profile.your_name == "Custom Name"
    assert prompt_builder.profile.your_title == "Custom Title"
    assert prompt_builder.profile.company_name == "Custom Company" 