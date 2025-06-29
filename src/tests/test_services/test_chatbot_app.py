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

def test_yaml_template_loading_and_matching():
    """Test that YAML templates load correctly and embedding matching works with template content and metadata."""
    from src.services.scroll_retriever import ScrollRetriever
    from src.services.prompt_builder import PromptBuilder
    from src.services.chat_history_manager import ChatHistoryManager, MessageType
    from src.services.llm_service import LLMService
    
    # Initialize services
    retriever = ScrollRetriever()
    chat_manager = ChatHistoryManager()
    
    # Mock LLM service for testing
    with patch('src.services.llm_service.LLMService') as mock_llm_class:
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        prompt_builder = PromptBuilder(
            scroll_retriever=retriever,
            llm_service=mock_llm,
            chat_history_manager=chat_manager
        )
    
    # Load YAML templates
    count = retriever.load_snippets()
    assert count > 0, f"Expected to load YAML templates, but got {count}"
    
    # Test 1: Verify YAML structure is loaded correctly
    assert len(retriever.snippets) > 0, "No snippets loaded"
    
    # Check first snippet has YAML structure
    first_snippet = retriever.snippets[0]
    assert hasattr(first_snippet, 'metadata'), "Snippet should have metadata from YAML"
    assert hasattr(first_snippet, 'template_content'), "Snippet should have template_content from YAML"
    assert hasattr(first_snippet, 'guidance'), "Snippet should have guidance from YAML"
    assert hasattr(first_snippet, 'content'), "Snippet should have content for matching"
    
    # Test 2: Test embedding matching with template content and metadata
    query = "I need to reach out to a music venue for a DJ gig"
    results = retriever.query(query, top_k=3, min_similarity=0.75)
    
    # Should find matches based on template content and metadata
    assert len(results) > 0, f"Expected to find matches for '{query}', but got {len(results)}"
    
    # Verify match quality
    snippet, similarity = results[0]
    assert similarity >= 0.75, f"Similarity should be >= 0.75, but got {similarity}"
    
    # Test 3: Test prompt enrichment with YAML guidance
    chat_manager.add_message(query, MessageType.INITIAL_PROMPT)
    
    prompt = prompt_builder.build_llm_prompt()
    
    # Check if template content and guidance are included
    assert "Subject:" in prompt, "Prompt should include template subject from YAML"
    assert "guidance" in prompt.lower() or "tone" in prompt.lower(), "Prompt should include template guidance from YAML"

def test_yaml_template_content_structure():
    """Test that YAML template content structure is properly parsed and used for matching."""
    from src.services.scroll_retriever import ScrollRetriever
    
    retriever = ScrollRetriever()
    count = retriever.load_snippets()
    assert count > 0, f"Expected to load YAML templates, but got {count}"
    
    # Test that each snippet has the correct structure
    for snippet in retriever.snippets:
        # Verify YAML structure
        assert snippet.metadata is not None, "Snippet should have metadata"
        assert snippet.template_content is not None, "Snippet should have template_content"
        assert snippet.guidance is not None, "Snippet should have guidance"
        assert snippet.content is not None, "Snippet should have content for matching"
        
        # Verify metadata fields
        metadata = snippet.metadata
        assert 'tags' in metadata, "Metadata should have tags"
        assert 'use_case' in metadata, "Metadata should have use_case"
        assert 'tone' in metadata, "Metadata should have tone"
        assert 'industry' in metadata, "Metadata should have industry"
        
        # Verify template content structure
        template = snippet.template_content
        assert isinstance(template, str), "Template content should be a string"
        assert len(template) > 0, "Template content should not be empty"
        
        # Verify guidance structure
        guidance = snippet.guidance
        assert isinstance(guidance, dict), "Guidance should be a dictionary"
        
        # Verify content for matching includes template content
        content = snippet.content
        assert isinstance(content, str), "Content should be a string"
        assert len(content) > 0, "Content should not be empty"
        
        # Content should include template content for matching (accounting for text processing)
        # The content is processed (whitespace normalized), so we check for key phrases instead of exact match
        template_key_phrases = [phrase.strip() for phrase in template.split() if len(phrase.strip()) > 3]
        content_key_phrases = [phrase.strip() for phrase in content.split() if len(phrase.strip()) > 3]
        
        # Check that at least some key phrases from template are in content
        matching_phrases = [phrase for phrase in template_key_phrases if phrase in content_key_phrases]
        assert len(matching_phrases) > 0, f"Content should include key phrases from template content. Template: {template[:100]}..., Content: {content[:100]}..." 