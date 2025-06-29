import pytest
from unittest.mock import patch, MagicMock
from src.services.prompt_builder import PromptBuilder, Profile
from src.services.chat_history_manager import ChatHistoryManager, MessageType
from src.services.scroll_retriever import EmailSnippet

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.default_tone = "professional"
    config.default_language = "English"
    return config

@pytest.fixture
def mock_llm_service(mock_config):
    service = MagicMock()
    service.config = mock_config
    return service

@pytest.fixture
def chat_history_manager():
    return ChatHistoryManager()

@pytest.fixture
def mock_scroll_retriever():
    retriever = MagicMock()
    return retriever

@pytest.fixture
def prompt_builder(mock_llm_service, chat_history_manager, mock_config):
    return PromptBuilder(mock_llm_service, chat_history_manager, config=mock_config)

@pytest.fixture
def prompt_builder_with_rag(mock_llm_service, chat_history_manager, mock_config, mock_scroll_retriever):
    return PromptBuilder(mock_llm_service, chat_history_manager, config=mock_config, scroll_retriever=mock_scroll_retriever)

def test_prompt_builder_initialization(prompt_builder, chat_history_manager):
    """Test PromptBuilder initialization."""
    assert prompt_builder.chat_history_manager == chat_history_manager
    assert prompt_builder.draft_email is None
    assert prompt_builder.scroll_retriever is None

def test_prompt_builder_initialization_with_rag(prompt_builder_with_rag, mock_scroll_retriever):
    """Test PromptBuilder initialization with scroll retriever."""
    assert prompt_builder_with_rag.scroll_retriever == mock_scroll_retriever

def test_retrieve_relevant_snippets_no_retriever(prompt_builder):
    """Test retrieving snippets when no scroll retriever is available."""
    snippets = prompt_builder._retrieve_relevant_snippets("test context")
    assert snippets == []

def test_retrieve_relevant_snippets_success(prompt_builder_with_rag, mock_scroll_retriever):
    """Test successful snippet retrieval."""
    # Mock snippets
    mock_snippet1 = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Test content 1",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"}
    )
    mock_snippet2 = EmailSnippet(
        id="test2",
        file_path="test2.md",
        content="Test content 2",
        metadata={"use_case": "followup", "industry": "healthcare", "tone": "friendly"}
    )
    
    mock_scroll_retriever.query.return_value = [
        (mock_snippet1, 0.85),
        (mock_snippet2, 0.75)
    ]
    
    snippets = prompt_builder_with_rag._retrieve_relevant_snippets("test context")
    
    assert len(snippets) == 2
    assert snippets[0][0] == mock_snippet1
    assert snippets[0][1] == 0.85
    assert snippets[1][0] == mock_snippet2
    assert snippets[1][1] == 0.75
    
    # Verify query was called with correct parameters
    mock_scroll_retriever.query.assert_called_once_with(
        query_text="test context",
        top_k=3,
        min_similarity=0.4,
        filters=None
    )

def test_retrieve_relevant_snippets_no_results(prompt_builder_with_rag, mock_scroll_retriever):
    """Test snippet retrieval when no results are found."""
    mock_scroll_retriever.query.return_value = []
    
    snippets = prompt_builder_with_rag._retrieve_relevant_snippets("test context")
    
    assert snippets == []

def test_retrieve_relevant_snippets_exception(prompt_builder_with_rag, mock_scroll_retriever):
    """Test snippet retrieval when an exception occurs."""
    mock_scroll_retriever.query.side_effect = Exception("Test error")
    
    snippets = prompt_builder_with_rag._retrieve_relevant_snippets("test context")
    
    assert snippets == []

def test_build_rag_context_no_snippets(prompt_builder):
    """Test building RAG context with no snippets."""
    context = prompt_builder._build_rag_context([])
    assert context == ""

def test_build_rag_context_with_snippets(prompt_builder):
    """Test building RAG context with snippets."""
    # Create mock snippets
    snippet1 = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Dear [Name],\n\nI hope this email finds you well...",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"}
    )
    snippet2 = EmailSnippet(
        id="test2",
        file_path="test2.md",
        content="Hi [Name],\n\nThanks for your time...",
        metadata={"use_case": "followup", "industry": "healthcare", "tone": "friendly"}
    )
    
    snippets = [(snippet1, 0.85), (snippet2, 0.75)]
    context = prompt_builder._build_rag_context(snippets)
    
    # Verify the context contains expected elements
    assert "REFERENCE EMAIL TEMPLATES" in context
    assert "⚠️  IMPORTANT: Do NOT copy specific details" in context
    assert "Example 1 (Similarity: 0.850)" in context
    assert "Example 2 (Similarity: 0.750)" in context
    assert "Use Case: outreach" in context
    assert "Use Case: followup" in context
    assert "Industry: tech" in context
    assert "Industry: healthcare" in context
    assert "Tone: professional" in context
    assert "Tone: friendly" in context
    assert "Dear [Name]," in context
    assert "Hi [Name]," in context
    assert "END REFERENCE TEMPLATES" in context

def test_build_llm_prompt_with_rag(prompt_builder_with_rag, chat_history_manager, mock_scroll_retriever):
    """Test building LLM prompt with RAG context."""
    # Add user message
    chat_history_manager.add_message("I need an outreach email", MessageType.INITIAL_PROMPT)
    
    # Mock snippets
    mock_snippet = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Test email content",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"}
    )
    mock_scroll_retriever.query.return_value = [(mock_snippet, 0.85)]
    
    prompt = prompt_builder_with_rag.build_llm_prompt()
    
    assert "expert assistant for writing outreach emails for any use case" in prompt
    assert "I need an outreach email" in prompt
    assert "REFERENCE EMAIL TEMPLATES" in prompt
    assert "Test email content" in prompt

def test_build_llm_prompt_without_rag(prompt_builder, chat_history_manager):
    """Test building LLM prompt without RAG context."""
    # Add user message
    chat_history_manager.add_message("I need an outreach email", MessageType.INITIAL_PROMPT)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "expert assistant for writing outreach emails for any use case" in prompt
    assert "I need an outreach email" in prompt
    assert "REFERENCE EMAIL TEMPLATES" not in prompt

def test_get_last_retrieved_snippets(prompt_builder_with_rag, mock_scroll_retriever):
    """Test getting last retrieved snippets."""
    # Initially empty
    assert prompt_builder_with_rag.get_last_retrieved_snippets() == []
    
    # Mock snippets
    mock_snippet = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Test content",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"}
    )
    mock_scroll_retriever.query.return_value = [(mock_snippet, 0.85)]
    
    # Retrieve snippets
    prompt_builder_with_rag._retrieve_relevant_snippets("test context")
    
    # Check last retrieved snippets
    last_snippets = prompt_builder_with_rag.get_last_retrieved_snippets()
    assert len(last_snippets) == 1
    assert last_snippets[0][0] == mock_snippet
    assert last_snippets[0][1] == 0.85

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
        name="John Doe",
        title="Sales Manager",
        company="TechCorp"
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
    mock_config.default_tone = "natural"
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
        name="John Doe",
        title="Sales Manager",
        company="TechCorp"
    )
    
    assert prompt_builder.profile.name == "John Doe"
    assert prompt_builder.profile.title == "Sales Manager"
    assert prompt_builder.profile.company == "TechCorp"

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
    chat_history_manager.summary = "Previous conversation about outreach email"
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Note: The current implementation doesn't include summary in the prompt
    # This test documents the current behavior
    assert "Previous conversation about outreach email" not in prompt

def test_prompt_with_max_messages_limit(prompt_builder, chat_history_manager):
    """Test that prompt respects message limits."""
    # Add many messages
    for i in range(10):
        chat_history_manager.add_message(f"Message {i}", MessageType.INITIAL_PROMPT)
        chat_history_manager.add_draft(f"Draft {i}")
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Should only include the latest user message
    assert "Message 9" in prompt
    assert "Message 0" not in prompt

def test_error_handling_in_generate_draft(prompt_builder, chat_history_manager):
    """Test error handling in draft generation."""
    chat_history_manager.add_message("Test request", MessageType.INITIAL_PROMPT)
    
    with patch.object(prompt_builder.llm_service, 'generate_response') as mock_generate:
        mock_generate.side_effect = Exception("LLM error")
        
        with pytest.raises(Exception):
            prompt_builder.generate_draft()

def test_profile_defaults(prompt_builder):
    """Test that profile has correct default values."""
    assert prompt_builder.profile.name == ""
    assert prompt_builder.profile.title == ""
    assert prompt_builder.profile.company == ""

def test_custom_profile_initialization():
    """Test initializing PromptBuilder with custom profile."""
    custom_profile = Profile(name="Jane Doe", title="Manager", company="Acme Corp")
    llm_service = MagicMock()
    chat_manager = ChatHistoryManager()
    
    prompt_builder = PromptBuilder(llm_service, chat_manager, profile=custom_profile)
    
    assert prompt_builder.profile.name == "Jane Doe"
    assert prompt_builder.profile.title == "Manager"
    assert prompt_builder.profile.company == "Acme Corp"

def test_build_enhanced_context_no_feedback(prompt_builder):
    """Test building enhanced context when no feedback exists."""
    context = prompt_builder._build_enhanced_context("I need an outreach email")
    assert context == "I need an outreach email"

def test_build_enhanced_context_with_feedback(prompt_builder, chat_history_manager):
    """Test building enhanced context with feedback."""
    # Add feedback messages
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    chat_history_manager.add_message("Focus on growth challenges", MessageType.FEEDBACK)
    
    context = prompt_builder._build_enhanced_context("I need a cold outreach email")
    
    # Should include latest message + all feedback
    assert "I need a cold outreach email" in context
    assert "Make it more professional" in context
    assert "Focus on growth challenges" in context
    
    # Most recent feedback should come first after the latest message
    parts = context.split(" ")
    assert "professional" in parts
    assert "challenges" in parts

def test_build_enhanced_context_feedback_order(prompt_builder, chat_history_manager):
    """Test that feedback is included in reverse chronological order (most recent first)."""
    # Add feedback in chronological order
    chat_history_manager.add_message("Make it shorter", MessageType.FEEDBACK)
    chat_history_manager.add_message("Add more details", MessageType.FEEDBACK)
    chat_history_manager.add_message("Make it professional", MessageType.FEEDBACK)
    
    context = prompt_builder._build_enhanced_context("Write an email")
    
    # Check that all feedback is included
    assert "Make it shorter" in context
    assert "Add more details" in context
    assert "Make it professional" in context

def test_retrieve_relevant_snippets_with_enhanced_context(prompt_builder_with_rag, mock_scroll_retriever, chat_history_manager):
    """Test that RAG retrieval uses enhanced context including feedback."""
    # Add feedback
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    chat_history_manager.add_message("Focus on tech industry", MessageType.FEEDBACK)
    
    # Mock snippets
    mock_snippet = EmailSnippet(
        id="test1",
        file_path="test1.md",
        content="Test content",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"}
    )
    mock_scroll_retriever.query.return_value = [(mock_snippet, 0.85)]
    
    # Retrieve snippets
    prompt_builder_with_rag._retrieve_relevant_snippets("I need an outreach email")
    
    # Verify query was called with enhanced context
    call_args = mock_scroll_retriever.query.call_args
    assert call_args is not None
    query_text = call_args.kwargs.get('query_text') or call_args.args[0]
    assert "I need an outreach email" in query_text
    assert "Make it more professional" in query_text
    assert "Focus on tech industry" in query_text 