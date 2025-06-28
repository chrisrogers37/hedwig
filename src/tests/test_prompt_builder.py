import pytest
from unittest.mock import Mock, patch
from services.prompt_builder import PromptBuilder, Profile
from services.llm_service import LLMService
from services.config_service import AppConfig
from services.chat_history_manager import ChatHistoryManager, MessageType
from services.scroll_retriever import ScrollRetriever, EmailSnippet

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
def mock_scroll_retriever():
    """Create a mock ScrollRetriever for testing."""
    return Mock(spec=ScrollRetriever)

@pytest.fixture
def prompt_builder(mock_llm_service, chat_history_manager, mock_config):
    """Create a fresh PromptBuilder instance for testing."""
    return PromptBuilder(mock_llm_service, chat_history_manager, config=mock_config)

@pytest.fixture
def prompt_builder_with_rag(mock_llm_service, chat_history_manager, mock_config, mock_scroll_retriever):
    """Create a PromptBuilder instance with RAG functionality for testing."""
    return PromptBuilder(mock_llm_service, chat_history_manager, config=mock_config, scroll_retriever=mock_scroll_retriever)

def test_prompt_builder_initialization(prompt_builder, chat_history_manager):
    """Test PromptBuilder initialization."""
    assert prompt_builder.llm_service is not None
    assert prompt_builder.chat_history_manager is chat_history_manager
    assert isinstance(prompt_builder.profile, Profile)

def test_prompt_builder_initialization_with_rag(prompt_builder_with_rag, mock_scroll_retriever):
    """Test PromptBuilder initialization with RAG functionality."""
    assert prompt_builder_with_rag.scroll_retriever is mock_scroll_retriever
    assert prompt_builder_with_rag.last_retrieved_snippets == []

def test_retrieve_relevant_snippets_no_retriever(prompt_builder):
    """Test snippet retrieval when no retriever is available."""
    snippets = prompt_builder._retrieve_relevant_snippets("test query")
    assert snippets == []

def test_retrieve_relevant_snippets_success(prompt_builder_with_rag, mock_scroll_retriever):
    """Test successful snippet retrieval."""
    # Create mock snippets
    mock_snippet1 = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Test content 1",
        metadata={
            "use_case": "cold_outreach",
            "industry": "technology",
            "tone": "professional"
        }
    )
    mock_snippet2 = EmailSnippet(
        id="test2", 
        file_path="test2.md",
        content="Test content 2",
        metadata={
            "use_case": "follow_up",
            "industry": "finance",
            "tone": "casual"
        }
    )
    
    # Mock the query method
    mock_scroll_retriever.query.return_value = [
        (mock_snippet1, 0.85),
        (mock_snippet2, 0.72)
    ]
    
    snippets = prompt_builder_with_rag._retrieve_relevant_snippets("test query")
    
    # Verify query was called with correct parameters
    mock_scroll_retriever.query.assert_called_once_with(
        query_text="test query",
        top_k=3,
        min_similarity=0.4,
        filters=None
    )
    
    # Verify results
    assert len(snippets) == 2
    assert snippets[0][0] == mock_snippet1
    assert snippets[0][1] == 0.85
    assert snippets[1][0] == mock_snippet2
    assert snippets[1][1] == 0.72
    
    # Verify snippets were stored
    assert prompt_builder_with_rag.last_retrieved_snippets == snippets

def test_retrieve_relevant_snippets_no_results(prompt_builder_with_rag, mock_scroll_retriever):
    """Test snippet retrieval when no relevant snippets are found."""
    mock_scroll_retriever.query.return_value = []
    
    snippets = prompt_builder_with_rag._retrieve_relevant_snippets("test query")
    
    assert snippets == []
    assert prompt_builder_with_rag.last_retrieved_snippets == []

def test_retrieve_relevant_snippets_exception(prompt_builder_with_rag, mock_scroll_retriever):
    """Test snippet retrieval when an exception occurs."""
    mock_scroll_retriever.query.side_effect = Exception("Test error")
    
    snippets = prompt_builder_with_rag._retrieve_relevant_snippets("test query")
    
    assert snippets == []

def test_build_rag_context_no_snippets(prompt_builder):
    """Test building RAG context with no snippets."""
    context = prompt_builder._build_rag_context([])
    assert context == ""

def test_build_rag_context_with_snippets(prompt_builder):
    """Test building RAG context with snippets."""
    mock_snippet1 = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Dear [Name],\n\nI hope this email finds you well...",
        metadata={
            "use_case": "cold_outreach",
            "industry": "technology",
            "tone": "professional"
        }
    )
    mock_snippet2 = EmailSnippet(
        id="test2",
        file_path="test2.md",
        content="Hi [Name],\n\nThanks for your time...",
        metadata={
            "use_case": "follow_up", 
            "industry": "finance",
            "tone": "casual"
        }
    )
    
    snippets = [(mock_snippet1, 0.85), (mock_snippet2, 0.72)]
    context = prompt_builder._build_rag_context(snippets)
    
    # Verify important instructions are included
    assert "REFERENCE EMAIL TEMPLATES" in context
    assert "Do NOT copy specific details from these templates" in context
    assert "Use these examples ONLY for" in context
    assert "END REFERENCE TEMPLATES" in context
    
    # Verify snippet content is included
    assert "Example 1 (Similarity: 0.850)" in context
    assert "Example 2 (Similarity: 0.720)" in context
    assert "cold_outreach" in context
    assert "technology" in context
    assert "professional" in context
    assert "follow_up" in context
    assert "finance" in context
    assert "casual" in context
    assert "Dear [Name]," in context
    assert "Hi [Name]," in context

def test_build_llm_prompt_with_rag(prompt_builder_with_rag, chat_history_manager, mock_scroll_retriever):
    """Test building LLM prompt with RAG functionality."""
    # Add user message
    chat_history_manager.add_message("I need a cold outreach email for a tech company", MessageType.INITIAL_PROMPT)
    
    # Mock snippet retrieval
    mock_snippet = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Dear [Name],\n\nI hope this email finds you well...",
        metadata={
            "use_case": "cold_outreach",
            "industry": "technology", 
            "tone": "professional"
        }
    )
    mock_scroll_retriever.query.return_value = [(mock_snippet, 0.85)]
    
    prompt = prompt_builder_with_rag.build_llm_prompt()
    
    # Verify RAG context is included
    assert "REFERENCE EMAIL TEMPLATES" in prompt
    assert "Do NOT copy specific details" in prompt
    assert "Use the reference templates above ONLY for style and structure guidance" in prompt
    assert "Write a completely original email" in prompt
    
    # Verify snippet was retrieved
    mock_scroll_retriever.query.assert_called_once()

def test_build_llm_prompt_without_rag(prompt_builder, chat_history_manager):
    """Test building LLM prompt without RAG functionality."""
    chat_history_manager.add_message("I need a cold outreach email", MessageType.INITIAL_PROMPT)
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Verify RAG context is not included
    assert "REFERENCE EMAIL TEMPLATES" not in prompt
    assert "Do NOT copy specific details" not in prompt

def test_get_last_retrieved_snippets(prompt_builder_with_rag, mock_scroll_retriever):
    """Test getting last retrieved snippets."""
    mock_snippet = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Test content",
        metadata={
            "use_case": "cold_outreach",
            "industry": "technology",
            "tone": "professional"
        }
    )
    
    # Set up mock retrieval
    mock_scroll_retriever.query.return_value = [(mock_snippet, 0.85)]
    
    # Retrieve snippets
    prompt_builder_with_rag._retrieve_relevant_snippets("test query")
    
    # Get last retrieved snippets
    last_snippets = prompt_builder_with_rag.get_last_retrieved_snippets()
    
    assert len(last_snippets) == 1
    assert last_snippets[0][0] == mock_snippet
    assert last_snippets[0][1] == 0.85

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
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    
    # Mock LLM response
    mock_draft = "Dear [Recipient Name],\n\nI hope this email finds you well..."
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.return_value = mock_draft
        
        draft = prompt_builder.generate_draft()
        
        assert draft == mock_draft
        
        # Verify the prompt included feedback
        call_args = mock_generate.call_args[0][0]
        assert "Make it more professional" in call_args

def test_update_profile(prompt_builder):
    """Test updating user profile."""
    prompt_builder.update_profile(
        your_name="John Doe",
        your_title="Sales Manager",
        company_name="TechCorp"
    )
    
    assert prompt_builder.profile.your_name == "John Doe"
    assert prompt_builder.profile.your_title == "Sales Manager"
    assert prompt_builder.profile.company_name == "TechCorp"

def test_get_draft_email(prompt_builder):
    """Test getting the current draft email."""
    # Initially no draft
    assert prompt_builder.get_draft_email() is None
    
    # Set a draft
    prompt_builder.draft_email = "Test draft email"
    assert prompt_builder.get_draft_email() == "Test draft email"

def test_prompt_includes_conversation_summary(prompt_builder, chat_history_manager):
    """Test that the prompt includes relevant conversation context."""
    # Add a conversation
    chat_history_manager.add_message("I need an email for a tech startup", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("Here's a draft...")
    chat_history_manager.add_message("Focus on their growth challenges", MessageType.FEEDBACK)
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Should include the latest feedback
    assert "Focus on their growth challenges" in prompt
    assert "Most recent feedback from user:" in prompt

def test_prompt_with_max_messages_limit(prompt_builder, chat_history_manager):
    """Test that the prompt handles conversation history appropriately."""
    # Add multiple messages
    for i in range(5):
        chat_history_manager.add_message(f"Message {i}", MessageType.INITIAL_PROMPT)
        chat_history_manager.add_draft(f"Draft {i}")
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Should only include the latest user message
    assert "Message 4" in prompt
    assert "Message 0" not in prompt
    assert "Message 1" not in prompt

def test_error_handling_in_generate_draft(prompt_builder, chat_history_manager):
    """Test error handling during draft generation."""
    chat_history_manager.add_message("Test message", MessageType.INITIAL_PROMPT)
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.side_effect = Exception("LLM service error")
        
        with pytest.raises(Exception):
            prompt_builder.generate_draft()

def test_profile_defaults(prompt_builder):
    """Test that profile has appropriate defaults."""
    assert prompt_builder.profile.your_name == ""
    assert prompt_builder.profile.your_title == ""
    assert prompt_builder.profile.company_name == ""

def test_custom_profile_initialization():
    """Test initializing PromptBuilder with a custom profile."""
    custom_profile = Profile(
        your_name="Jane Doe",
        your_title="VP Sales",
        company_name="CustomCorp"
    )
    
    with patch('services.llm_service.LLMService'), patch('services.chat_history_manager.ChatHistoryManager'):
        prompt_builder = PromptBuilder(
            Mock(), Mock(), 
            profile=custom_profile
        )
        
        assert prompt_builder.profile.your_name == "Jane Doe"
        assert prompt_builder.profile.your_title == "VP Sales"
        assert prompt_builder.profile.company_name == "CustomCorp" 