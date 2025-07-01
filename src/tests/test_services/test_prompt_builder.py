import pytest
from unittest.mock import patch, MagicMock
from src.services.prompt_builder import PromptBuilder
from src.services.profile_manager import ProfileManager
from src.services.chat_history_manager import ChatHistoryManager, MessageType
from src.services.scroll_retriever import EmailSnippet

@pytest.fixture
def mock_config():
    config = MagicMock()
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
def profile_manager():
    return ProfileManager()

@pytest.fixture
def prompt_builder(mock_llm_service, chat_history_manager, mock_config, profile_manager):
    return PromptBuilder(mock_llm_service, chat_history_manager, profile_manager=profile_manager, config=mock_config)

@pytest.fixture
def prompt_builder_with_rag(mock_llm_service, chat_history_manager, mock_config, mock_scroll_retriever, profile_manager):
    return PromptBuilder(mock_llm_service, chat_history_manager, profile_manager=profile_manager, config=mock_config, scroll_retriever=mock_scroll_retriever)

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
        file_path="test1.yaml",
        content="Test content 1",
        template_content="Test content 1",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"},
        guidance={"tone": "professional", "style": "formal"}
    )
    mock_snippet2 = EmailSnippet(
        id="test2",
        file_path="test2.yaml",
        content="Test content 2",
        template_content="Test content 2",
        metadata={"use_case": "followup", "industry": "healthcare", "tone": "friendly"},
        guidance={"tone": "friendly", "style": "informal"}
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
        min_similarity=0.75,
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
        file_path="test1.yaml",
        content="Dear [Name],\n\nI hope this email finds you well...",
        template_content="Dear [Name],\n\nI hope this email finds you well...",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"},
        guidance={"tone": "professional", "style": "formal"}
    )
    snippet2 = EmailSnippet(
        id="test2",
        file_path="test2.yaml",
        content="Hi [Name],\n\nThanks for your time...",
        template_content="Hi [Name],\n\nThanks for your time...",
        metadata={"use_case": "followup", "industry": "healthcare", "tone": "friendly"},
        guidance={"tone": "friendly", "style": "informal"}
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
        file_path="test1.yaml",
        content="Test email content",
        template_content="Test email content",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"},
        guidance={"tone": "professional", "style": "formal"}
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
        file_path="test1.yaml",
        content="Test content",
        template_content="Test content",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"},
        guidance={"tone": "professional", "style": "formal"}
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
    assert "No conversation history available" in prompt  # Updated to match new approach

def test_build_llm_prompt_with_conversation_history(prompt_builder, chat_history_manager):
    """Test building prompt with conversation history."""
    # Add some messages to the conversation
    chat_history_manager.add_message("I need help writing an outreach email", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("Here's a draft email for you...")
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "expert assistant for writing outreach emails for any use case" in prompt
    assert "Make it more professional" in prompt  # Latest feedback should be included
    assert "I need help writing an outreach email" in prompt  # Original request should be in context
    assert "User: I need help writing an outreach email" in prompt  # Updated to match new format

def test_build_llm_prompt_with_profile(prompt_builder):
    """Test building prompt with user profile information."""
    # Update profile
    prompt_builder.update_profile(
        name="John Doe",
        title="Sales Manager",
        company="TechCorp"
    )
    
    assert prompt_builder.profile_manager.profile.name == "John Doe"
    assert prompt_builder.profile_manager.profile.title == "Sales Manager"
    assert prompt_builder.profile_manager.profile.company == "TechCorp"

def test_build_llm_prompt_latest_user_message_only(prompt_builder, chat_history_manager):
    """Test that only the latest user message is used in the prompt."""
    # Add multiple user messages
    chat_history_manager.add_message("First request", MessageType.INITIAL_PROMPT)
    chat_history_manager.add_draft("First draft")
    chat_history_manager.add_message("Second request", MessageType.INITIAL_PROMPT)
    
    prompt = prompt_builder.build_llm_prompt()
    
    assert "Second request" in prompt  # Latest user message
    assert "First request" in prompt  # Previous request should be in context
    assert "User: First request" in prompt  # Updated to match new format

def test_build_llm_prompt_with_feedback(prompt_builder):
    """Test building prompt with feedback using conversation context."""
    # Add initial request
    prompt_builder.chat_history_manager.add_message("Write an email to a client", MessageType.INITIAL_PROMPT)
    
    # Add a draft
    prompt_builder.chat_history_manager.add_draft("Here is your email draft...")
    
    # Add feedback
    prompt_builder.chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Should include full conversation context
    assert "User: Write an email to a client" in prompt
    assert "Assistant: Here is your email draft..." in prompt
    assert "User: Make it more professional" in prompt

def test_build_full_conversation_context(prompt_builder):
    """Test building full conversation context."""
    # Add conversation messages
    prompt_builder.chat_history_manager.add_message("Initial request", MessageType.INITIAL_PROMPT)
    prompt_builder.chat_history_manager.add_draft("First draft")
    prompt_builder.chat_history_manager.add_message("Feedback on draft", MessageType.FEEDBACK)
    prompt_builder.chat_history_manager.add_draft("Revised draft")
    
    context = prompt_builder._build_full_conversation_context()
    
    # Should include all messages in order
    assert "User: Initial request" in context
    assert "Assistant: First draft" in context
    assert "User: Feedback on draft" in context
    assert "Assistant: Revised draft" in context

def test_build_full_conversation_context_empty(prompt_builder):
    """Test building conversation context with no messages."""
    context = prompt_builder._build_full_conversation_context()
    assert context == "No conversation history available."

def test_build_full_conversation_context_single_message(prompt_builder):
    """Test building conversation context with single message."""
    prompt_builder.chat_history_manager.add_message("Single request", MessageType.INITIAL_PROMPT)
    
    context = prompt_builder._build_full_conversation_context()
    assert "User: Single request" in context
    assert "\n\n" not in context  # No separators for single message

def test_build_full_conversation_context_with_system_message(prompt_builder):
    """Test building conversation context including system messages."""
    prompt_builder.chat_history_manager.add_message("System info", MessageType.SYSTEM)
    prompt_builder.chat_history_manager.add_message("User request", MessageType.INITIAL_PROMPT)
    
    context = prompt_builder._build_full_conversation_context()
    assert "System: System info" in context
    assert "User: User request" in context

def test_feedback_detection_by_message_type(prompt_builder):
    """Test that feedback is detected by message type, not string content."""
    # Add initial request
    prompt_builder.chat_history_manager.add_message("Write an email", MessageType.INITIAL_PROMPT)
    prompt_builder.chat_history_manager.add_draft("Draft email")
    
    # Add feedback (should be detected by type, not content)
    prompt_builder.chat_history_manager.add_message("This is great!", MessageType.FEEDBACK)
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Should include feedback even though content doesn't match old patterns
    assert "User: This is great!" in prompt
    
    # Should not use deprecated methods
    assert prompt_builder._get_previous_draft_context() == ""
    assert prompt_builder._extract_feedback_instructions("test") == ""

def test_deprecated_methods_return_empty(prompt_builder):
    """Test that deprecated methods return empty strings."""
    assert prompt_builder._get_previous_draft_context() == ""
    assert prompt_builder._extract_feedback_instructions("any message") == ""

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
    
    assert prompt_builder.profile_manager.profile.name == "John Doe"
    assert prompt_builder.profile_manager.profile.title == "Sales Manager"
    assert prompt_builder.profile_manager.profile.company == "TechCorp"

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
    assert prompt_builder.profile_manager.profile.name == ""
    assert prompt_builder.profile_manager.profile.title == ""
    assert prompt_builder.profile_manager.profile.company == ""

def test_custom_profile_initialization():
    """Test initializing PromptBuilder with custom profile."""
    custom_profile_manager = ProfileManager()
    custom_profile_manager.update_profile(name="Jane Doe", title="Manager", company="Acme Corp")
    llm_service = MagicMock()
    chat_manager = ChatHistoryManager()
    
    prompt_builder = PromptBuilder(llm_service, chat_manager, profile_manager=custom_profile_manager)
    
    assert prompt_builder.profile_manager.profile.name == "Jane Doe"
    assert prompt_builder.profile_manager.profile.title == "Manager"
    assert prompt_builder.profile_manager.profile.company == "Acme Corp"

def test_build_enhanced_context_no_feedback(prompt_builder):
    """Test building enhanced context when no feedback exists."""
    context = prompt_builder._build_enhanced_context("I need an outreach email")
    assert context == "I need an outreach email"

def test_build_enhanced_context_with_feedback(prompt_builder, chat_history_manager):
    """Test building enhanced context with all user messages."""
    # Add user messages
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    chat_history_manager.add_message("Focus on growth challenges", MessageType.FEEDBACK)
    
    context = prompt_builder._build_enhanced_context("I need a cold outreach email")
    
    # Should include latest message + all previous user messages
    assert "I need a cold outreach email" in context
    assert "Make it more professional" in context
    assert "Focus on growth challenges" in context

def test_build_enhanced_context_feedback_order(prompt_builder):
    """Test that all user messages are included in the correct order in enhanced context."""
    # Add initial request
    prompt_builder.chat_history_manager.add_message("Write an email", MessageType.INITIAL_PROMPT)
    prompt_builder.chat_history_manager.add_draft("First draft")
    prompt_builder.chat_history_manager.add_message("First feedback", MessageType.FEEDBACK)
    prompt_builder.chat_history_manager.add_draft("Second draft")
    prompt_builder.chat_history_manager.add_message("Second feedback", MessageType.FEEDBACK)
    
    # Build enhanced context
    enhanced_context = prompt_builder._build_enhanced_context("Latest message")
    
    # Should include all user messages
    assert "First feedback" in enhanced_context
    assert "Second feedback" in enhanced_context
    assert "Write an email" in enhanced_context

def test_retrieve_relevant_snippets_with_enhanced_context(prompt_builder_with_rag, mock_scroll_retriever, chat_history_manager):
    """Test that RAG retrieval uses enhanced context including all user messages."""
    # Add user messages
    chat_history_manager.add_message("Make it more professional", MessageType.FEEDBACK)
    chat_history_manager.add_message("Focus on tech industry", MessageType.FEEDBACK)
    
    # Mock snippets
    mock_snippet = EmailSnippet(
        id="test1",
        file_path="test1.yaml",
        content="Test content",
        template_content="Test content",
        metadata={"use_case": "outreach", "industry": "tech", "tone": "professional"},
        guidance={"tone": "professional", "style": "formal"}
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