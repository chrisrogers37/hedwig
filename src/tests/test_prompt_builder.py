import pytest
from unittest.mock import Mock, patch
from src.services.prompt_builder import PromptBuilder, Profile
from src.services.llm_service import LLMService
from src.services.config_service import AppConfig
from src.services.chat_history_manager import ChatHistoryManager, MessageType

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
def chat_history_manager():
    """Create a fresh ChatHistoryManager instance for testing."""
    return ChatHistoryManager()

@pytest.fixture
def prompt_builder(mock_llm_service, chat_history_manager):
    """Create a fresh PromptBuilder instance for testing."""
    return PromptBuilder(mock_llm_service, chat_history_manager)

def test_prompt_builder_initialization(prompt_builder, chat_history_manager):
    """Test PromptBuilder initialization."""
    assert prompt_builder.llm_service is not None
    assert prompt_builder.chat_history_manager is chat_history_manager
    assert isinstance(prompt_builder.profile, Profile)

def test_build_llm_prompt_with_empty_history(prompt_builder):
    """Test building prompt with empty conversation history."""
    prompt = prompt_builder.build_llm_prompt()
    
    assert "expert assistant for writing sales outreach emails" in prompt
    assert "Conversation so far:" in prompt
    assert "[No profile info provided]" in prompt

def test_build_llm_prompt_with_conversation_history(prompt_builder, chat_history_manager):
    """Test building prompt with conversation history."""
    # Add some messages to the conversation
    chat_history_manager.add_message("I need help writing an outreach email", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("Here's a draft email for you...")
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "expert assistant for writing sales outreach emails" in prompt
    assert "I need help writing an outreach email" in prompt
    assert "Here's a draft email for you..." in prompt
    assert "Make it more professional" in prompt

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
    """Test that prompt includes conversation summary when available."""
    # Add messages and create a summary
    chat_history_manager.add_message("Initial request", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("First draft")
    chat_history_manager.add_message("Feedback", MessageType.FEEDBACK)
    
    # Create a summary
    chat_history_manager.summary = "Previous conversation about outreach email with feedback"
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "CONVERSATION SUMMARY:" in prompt
    assert "Previous conversation about outreach email with feedback" in prompt

def test_prompt_with_max_messages_limit(prompt_builder, chat_history_manager):
    """Test that prompt respects max_messages parameter."""
    # Add many messages
    for i in range(10):
        chat_history_manager.add_message(f"Message {i}", MessageType.INITIAL_PROMPT)
        chat_history_manager.add_draft(f"Draft {i}")
    
    # Get context with limited messages
    context = chat_history_manager.get_conversation_context(max_messages=5)
    prompt = prompt_builder.build_llm_prompt()
    
    # Should include the conversation context (which respects the limit)
    assert "Conversation so far:" in prompt

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