"""
Comprehensive tests for the Review Agent

Tests all components: review_types, review_prompts, review_parser, and review_agent.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.services.review_agent.review_types import (
    FeedbackItem, 
    ReviewResult, 
    create_feedback_item
)
from src.services.review_agent.review_prompts import build_review_prompt
from src.services.review_agent.review_parser import ReviewResponseParser
from src.services.review_agent.review_agent import ReviewAgent
from src.services.llm_service import LLMService


class TestReviewTypes:
    """Test cases for review_types module."""
    
    def test_feedback_item_creation(self):
        """Test FeedbackItem creation and basic functionality."""
        feedback = FeedbackItem(
            id="test_1",
            text="Add specific details about the collaboration"
        )
        
        assert feedback.id == "test_1"
        assert feedback.text == "Add specific details about the collaboration"
        assert isinstance(feedback.timestamp, datetime)

    def test_feedback_item_to_dict(self):
        """Test FeedbackItem serialization to dictionary."""
        feedback = FeedbackItem(
            id="test_1",
            text="Test feedback text"
        )
        
        data = feedback.to_dict()
        
        assert data["id"] == "test_1"
        assert data["text"] == "Test feedback text"
        assert "timestamp" in data

    def test_feedback_item_from_dict(self):
        """Test FeedbackItem deserialization from dictionary."""
        timestamp = datetime.now().isoformat()
        data = {
            "id": "test_1",
            "text": "Test feedback text",
            "timestamp": timestamp
        }
        
        feedback = FeedbackItem.from_dict(data)
        
        assert feedback.id == "test_1"
        assert feedback.text == "Test feedback text"
        assert feedback.timestamp.isoformat() == timestamp

    def test_feedback_item_str_representation(self):
        """Test FeedbackItem string representation."""
        feedback = FeedbackItem(
            id="test_1",
            text="Test feedback"
        )
        
        assert str(feedback) == "Feedback test_1: Test feedback"

    def test_review_result_creation(self):
        """Test ReviewResult creation and basic functionality."""
        result = ReviewResult(
            email_content="Test email content",
            critique="This is a test critique",
            should_regenerate=False
        )
        
        assert result.email_content == "Test email content"
        assert result.critique == "This is a test critique"
        assert result.should_regenerate == False
        assert len(result.actionable_feedback) == 0
        assert isinstance(result.timestamp, datetime)

    def test_review_result_add_feedback_item(self):
        """Test adding feedback items to ReviewResult."""
        result = ReviewResult(
            email_content="Test email",
            critique="Test critique"
        )
        
        feedback = FeedbackItem(
            id="test_1",
            text="Test feedback"
        )
        
        result.add_feedback_item(feedback)
        
        assert len(result.actionable_feedback) == 1
        assert result.actionable_feedback[0].id == "test_1"

    def test_review_result_get_clickable_feedback(self):
        """Test getting clickable feedback items."""
        result = ReviewResult(
            email_content="Test email",
            critique="Test critique"
        )
        feedback1 = FeedbackItem(
            id="test_1",
            text="Test feedback 1"
        )
        feedback2 = FeedbackItem(
            id="test_2",
            text="Test feedback 2"
        )
        result.add_feedback_item(feedback1)
        result.add_feedback_item(feedback2)
        clickable_feedback = result.get_clickable_feedback()
        assert len(clickable_feedback) == 2
        assert feedback1 in clickable_feedback
        assert feedback2 in clickable_feedback

    def test_review_result_to_dict(self):
        """Test ReviewResult serialization to dictionary."""
        result = ReviewResult(
            email_content="Test email",
            critique="Test critique",
            should_regenerate=True,
            template_info={"industry": "tech"},
            user_context="Test context"
        )
        
        feedback = FeedbackItem(
            id="test_1",
            text="Test feedback"
        )
        result.add_feedback_item(feedback)
        
        data = result.to_dict()
        
        assert data["email_content"] == "Test email"
        assert data["critique"] == "Test critique"
        assert data["should_regenerate"] == True
        assert data["template_info"] == {"industry": "tech"}
        assert data["user_context"] == "Test context"
        assert len(data["actionable_feedback"]) == 1
        assert data["actionable_feedback"][0]["id"] == "test_1"

    def test_review_result_from_dict(self):
        """Test ReviewResult deserialization from dictionary."""
        timestamp = datetime.now().isoformat()
        data = {
            "email_content": "Test email",
            "critique": "Test critique",
            "actionable_feedback": [{
                "id": "test_1",
                "text": "Test feedback",
                "timestamp": timestamp
            }],
            "should_regenerate": True,
            "template_info": {"industry": "tech"},
            "user_context": "Test context",
            "timestamp": timestamp
        }
        
        result = ReviewResult.from_dict(data)
        
        assert result.email_content == "Test email"
        assert result.critique == "Test critique"
        assert result.should_regenerate == True
        assert result.template_info == {"industry": "tech"}
        assert result.user_context == "Test context"
        assert len(result.actionable_feedback) == 1
        assert result.actionable_feedback[0].id == "test_1"

    def test_review_result_str_representation(self):
        """Test ReviewResult string representation."""
        result = ReviewResult(
            email_content="Test email",
            critique="Test critique",
            should_regenerate=True
        )
        
        feedback = FeedbackItem(
            id="test_1",
            text="Test feedback"
        )
        result.add_feedback_item(feedback)
        
        assert str(result) == "Review: 1 feedback items, regenerate: True"

    def test_create_feedback_item_helper(self):
        """Test the create_feedback_item helper function."""
        feedback = create_feedback_item(
            text="Test feedback text",
            feedback_id="custom_id"
        )
        
        assert feedback.id == "custom_id"
        assert feedback.text == "Test feedback text"

    def test_create_feedback_item_auto_id(self):
        """Test create_feedback_item with auto-generated ID."""
        feedback = create_feedback_item(
            text="Test feedback text"
        )
        
        assert feedback.id.startswith("feedback_")
        assert feedback.text == "Test feedback text"


class TestReviewPrompts:
    """Test cases for review_prompts module."""
    
    def test_build_review_prompt_basic(self):
        """Test basic prompt building without optional parameters."""
        email_content = "Hi there, I hope this email finds you well."
        
        prompt = build_review_prompt(email_content=email_content)
        
        assert "Hi there, I hope this email finds you well." in prompt
        assert "## CRITIQUE" in prompt
        assert "## FEEDBACK" in prompt
        assert "## RECOMMENDATION" in prompt
        assert "the recipient industry" in prompt  # Default industry

    def test_build_review_prompt_with_template_info(self):
        """Test prompt building with template information."""
        email_content = "Test email content"
        template_info = {
            "industry": "healthcare",
            "forbidden_phrases": ["synergy", "leverage"],
            "writing_tips": ["Be professional", "Be concise"],
            "preferred_phrases": ["collaboration", "partnership"],
            "structure": "Introduction, Value Proposition, Call to Action"
        }
        
        prompt = build_review_prompt(
            email_content=email_content,
            template_info=template_info
        )
        
        assert "healthcare" in prompt
        assert "synergy" in prompt
        assert "leverage" in prompt
        assert "collaboration" in prompt
        assert "partnership" in prompt
        assert "Be professional" in prompt
        assert "Be concise" in prompt
        assert "Introduction, Value Proposition, Call to Action" in prompt

    def test_build_review_prompt_with_user_context(self):
        """Test prompt building with user context."""
        email_content = "Test email content"
        user_context = "User wants to reach out to potential clients"
        
        prompt = build_review_prompt(
            email_content=email_content,
            user_context=user_context
        )
        
        assert "User wants to reach out to potential clients" in prompt

    def test_build_review_prompt_with_recipient_industry(self):
        """Test prompt building with specific recipient industry."""
        email_content = "Test email content"
        recipient_industry = "technology"
        
        prompt = build_review_prompt(
            email_content=email_content,
            recipient_industry=recipient_industry
        )
        
        assert "technology" in prompt

    def test_build_review_prompt_with_extra_metadata(self):
        """Test prompt building with extra metadata."""
        email_content = "Test email content"
        extra_metadata = {
            "email_type": "cold_outreach",
            "target_role": "CTO",
            "company_size": "50-200 employees"
        }
        
        prompt = build_review_prompt(
            email_content=email_content,
            extra_metadata=extra_metadata
        )
        
        assert "email_type: cold_outreach" in prompt
        assert "target_role: CTO" in prompt
        assert "company_size: 50-200 employees" in prompt

    def test_build_review_prompt_complete(self):
        """Test prompt building with all parameters."""
        email_content = "Test email content"
        template_info = {"industry": "tech", "forbidden_phrases": ["synergy"]}
        user_context = "Cold outreach to startup"
        recipient_industry = "fintech"
        extra_metadata = {"urgency": "high"}
        
        prompt = build_review_prompt(
            email_content=email_content,
            template_info=template_info,
            user_context=user_context,
            recipient_industry=recipient_industry,
            extra_metadata=extra_metadata
        )
        
        # Should use recipient_industry over template_info industry
        assert "fintech" in prompt
        assert "synergy" in prompt
        assert "Cold outreach to startup" in prompt
        assert "urgency: high" in prompt


class TestReviewParser:
    """Test cases for review_parser module."""
    
    @pytest.fixture
    def parser(self):
        """Create a ReviewResponseParser instance."""
        return ReviewResponseParser()
    
    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response for testing."""
        return """
        ## CRITIQUE
        This email has a good basic structure and professional tone. The opening is appropriate and the message is clear. However, it lacks specific details about the collaboration opportunity and could benefit from more personalization.
        
        ## FEEDBACK
         - Add specific details about the collaboration opportunity
         - Include more personalization based on the recipient's background
         - Consider adding a clear call-to-action
        
        ## RECOMMENDATION
        KEEP
        """
    
    def test_parser_initialization(self, parser):
        """Test parser initialization."""
        assert parser.critique_pattern is not None
        assert parser.feedback_pattern is not None
        assert parser.recommendation_pattern is not None

    def test_extract_critique_success(self, parser, sample_llm_response):
        """Test successful critique extraction."""
        critique = parser._extract_critique(sample_llm_response)
        
        assert "This email has a good basic structure" in critique
        assert "lacks specific details" in critique
        assert "could benefit from more personalization" in critique

    def test_extract_critique_fallback(self, parser):
        """Test critique extraction fallback when section not found."""
        llm_response = """
        This is a general review without structured sections.
        The email needs improvement in several areas.
        It should be more specific and personal.
        """
        
        critique = parser._extract_critique(llm_response)
        
        assert "general review without structured sections" in critique
        assert "needs improvement in several areas" in critique

    def test_extract_actionable_feedback_success(self, parser, sample_llm_response):
        """Test successful actionable feedback extraction."""
        feedback_items = parser._extract_actionable_feedback(sample_llm_response)
        
        assert len(feedback_items) == 3
        assert feedback_items[0].text == "Add specific details about the collaboration opportunity"
        assert feedback_items[1].text == "Include more personalization based on the recipient's background"
        assert feedback_items[2].text == "Consider adding a clear call"

    def test_extract_actionable_feedback_no_section(self, parser):
        """Test feedback extraction when section not found."""
        llm_response = """
        ## CRITIQUE
        This is a critique without a feedback section.
        
        ## RECOMMENDATION
        KEEP
        """
        
        feedback_items = parser._extract_actionable_feedback(llm_response)
        
        assert len(feedback_items) == 0

    def test_split_feedback_items_bullets(self, parser):
        """Test splitting feedback items with bullet points."""
        feedback_text = """
         - First feedback item
         - Second feedback item
         - Third feedback item
        """
        
        items = parser._split_feedback_items(feedback_text)
        
        assert len(items) == 3
        assert items[0] == "First feedback item"
        assert items[1] == "Second feedback item"
        assert items[2] == "Third feedback item"

    def test_split_feedback_items_numbered(self, parser):
        """Test splitting feedback items with numbered lists."""
        feedback_text = """
         1. First feedback item
         2. Second feedback item
         3. Third feedback item
        """
        
        items = parser._split_feedback_items(feedback_text)
        
        assert len(items) == 3
        assert items[0] == "1. First feedback item"
        assert items[1] == "2. Second feedback item"
        assert items[2] == "3. Third feedback item"

    def test_split_feedback_items_mixed(self, parser):
        """Test splitting feedback items with mixed formats."""
        feedback_text = """
         • First feedback item
         - Second feedback item
         * Third feedback item
        """
        
        items = parser._split_feedback_items(feedback_text)
        
        assert len(items) == 3
        assert items[0] == "First feedback item"
        assert items[1] == "Second feedback item"
        assert items[2] == "Third feedback item"

    def test_split_feedback_items_limit(self, parser):
        """Test that feedback items are limited to 5."""
        feedback_text = """
         - This is a longer feedback item that should be included
         - Another substantial feedback item with enough content
         - Third feedback item with sufficient length to pass filter
         - Fourth feedback item that meets the minimum length requirement
         - Fifth feedback item with adequate content for inclusion
         - Sixth feedback item that should be filtered out due to limit
         - Seventh feedback item that should also be filtered out
        """
        
        items = parser._split_feedback_items(feedback_text)
        
        assert len(items) == 5
        assert "This is a longer feedback item" in items[0]
        assert "Fifth feedback item with adequate content" in items[4]

    def test_create_feedback_item_success(self, parser):
        """Test successful feedback item creation."""
        item_text = "Add specific details about the collaboration"
        
        feedback_item = parser._create_feedback_item(item_text, 0)
        
        assert feedback_item is not None
        assert feedback_item.id == "feedback_0"
        assert feedback_item.text == "Add specific details about the collaboration"

    def test_create_feedback_item_short_text(self, parser):
        """Test feedback item creation with short text (should be included)."""
        item_text = "Short"
        
        feedback_item = parser._create_feedback_item(item_text, 0)
        
        # Should be created because _create_feedback_item doesn't filter by length
        assert feedback_item is not None
        assert feedback_item.text == "Short"

    def test_should_regenerate_explicit_keep(self, parser):
        """Test regeneration decision with explicit KEEP."""
        llm_response = """
        ## RECOMMENDATION
        KEEP
        """
        
        should_regenerate = parser._should_regenerate(llm_response)
        
        assert should_regenerate == False

    def test_should_regenerate_explicit_regenerate(self, parser):
        """Test regeneration decision with explicit REGENERATE."""
        llm_response = """
        ## RECOMMENDATION
        REGENERATE
        """
        
        should_regenerate = parser._should_regenerate(llm_response)
        
        assert should_regenerate == True

    def test_should_regenerate_keywords(self, parser):
        """Test regeneration decision with keywords."""
        llm_response = """
        This email needs significant improvement and should be rewritten.
        """
        
        should_regenerate = parser._should_regenerate(llm_response)
        
        assert should_regenerate == True

    def test_should_regenerate_default(self, parser):
        """Test regeneration decision default behavior."""
        llm_response = """
        This is a neutral response without clear recommendation.
        """
        
        should_regenerate = parser._should_regenerate(llm_response)
        
        assert should_regenerate == False

    def test_parse_review_response_success(self, parser, sample_llm_response):
        """Test successful complete review response parsing."""
        email_content = "Test email content"
        
        result = parser.parse_review_response(
            llm_response=sample_llm_response,
            email_content=email_content,
            template_info={"industry": "tech"},
            user_context="Test context"
        )
        
        assert result.email_content == email_content
        assert "This email has a good basic structure" in result.critique
        assert len(result.actionable_feedback) == 3
        assert result.should_regenerate == False
        assert result.template_info == {"industry": "tech"}
        assert result.user_context == "Test context"

    def test_parse_review_response_fallback(self, parser):
        """Test review response parsing fallback when parsing fails."""
        email_content = "Test email content"
        llm_response = "Invalid response format"
        
        result = parser.parse_review_response(
            llm_response=llm_response,
            email_content=email_content
        )
        
        assert result.email_content == email_content
        assert "Invalid response format" in result.critique
        assert result.should_regenerate == False


class TestReviewAgent:
    """Test cases for review_agent module."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        mock_service = Mock(spec=LLMService)
        return mock_service
    
    @pytest.fixture
    def review_agent(self, mock_llm_service):
        """Create a ReviewAgent instance with mock dependencies."""
        agent = ReviewAgent(mock_llm_service)
        # Mock the parser
        agent.parser = Mock()
        return agent
    
    @pytest.fixture
    def sample_email_content(self):
        """Sample email content for testing."""
        return """
        Hi there,
        
        I hope this email finds you well. I wanted to reach out about a potential collaboration opportunity.
        
        Best regards,
        John
        """
    
    @pytest.fixture
    def sample_llm_response(self):
        """Sample structured LLM response for testing."""
        return """
        ## CRITIQUE
        This email has a good basic structure and professional tone. The opening is appropriate and the message is clear. However, it lacks specific details about the collaboration opportunity and could benefit from more personalization.
        
        ## FEEDBACK
         - Add specific details about the collaboration opportunity
         - Include more personalization based on the recipient's background
         - Consider adding a clear call-to-action
        
        ## RECOMMENDATION
        KEEP
        """

    def test_review_agent_initialization(self, review_agent):
        """Test that ReviewAgent initializes correctly."""
        assert review_agent.llm_service is not None
        assert review_agent.parser is not None

    def test_review_email_success(self, review_agent, sample_email_content, sample_llm_response):
        """Test successful email review process."""
        # Mock LLM service response
        review_agent.llm_service.generate_response.return_value = sample_llm_response
        
        # Mock parser response
        from src.services.review_agent.review_types import ReviewResult, FeedbackItem
        mock_result = ReviewResult(
            email_content=sample_email_content,
            critique="This email has a good basic structure...",
            should_regenerate=False
        )
        feedback_item = FeedbackItem(
            id="feedback_0",
            text="Add specific details about the collaboration opportunity"
        )
        mock_result.add_feedback_item(feedback_item)
        review_agent.parser.parse_review_response.return_value = mock_result
        
        # Call the method
        result = review_agent.review_email(
            email_content=sample_email_content,
            template_info={"industry": "tech"},
            user_context="Collaboration request"
        )
        
        # Verify LLM service was called
        review_agent.llm_service.generate_response.assert_called_once()
        
        # Verify parser was called
        review_agent.parser.parse_review_response.assert_called_once()
        
        # Verify result
        assert result.critique == "This email has a good basic structure..."
        assert result.should_regenerate == False
        assert len(result.actionable_feedback) == 1

    def test_review_email_llm_failure(self, review_agent, sample_email_content):
        """Test email review when LLM service fails."""
        # Mock LLM service failure
        review_agent.llm_service.generate_response.return_value = None
        
        # Call the method
        result = review_agent.review_email(email_content=sample_email_content)
        
        # Verify fallback result
        assert result.email_content == sample_email_content
        assert result.critique == "Review unavailable due to technical issues. Please check your email manually."
        assert result.should_regenerate == False

    def test_review_email_exception_handling(self, review_agent, sample_email_content):
        """Test email review exception handling."""
        # Mock LLM service to raise exception
        review_agent.llm_service.generate_response.side_effect = Exception("API Error")
        
        # Call the method
        result = review_agent.review_email(email_content=sample_email_content)
        
        # Verify fallback result
        assert result.email_content == sample_email_content
        assert result.critique == "Review unavailable due to technical issues. Please check your email manually."
        assert result.should_regenerate == False

    def test_get_critique(self, review_agent):
        """Test getting critique from review result."""
        from src.services.review_agent.review_types import ReviewResult
        
        mock_result = ReviewResult(
            email_content="test",
            critique="This is a detailed critique of the email."
        )
        
        critique = review_agent.get_critique(mock_result)
        assert critique == "This is a detailed critique of the email."

    def test_get_critique_empty(self, review_agent):
        """Test getting critique when empty."""
        from src.services.review_agent.review_types import ReviewResult
        
        mock_result = ReviewResult(
            email_content="test",
            critique=""
        )
        
        critique = review_agent.get_critique(mock_result)
        assert critique == "No critique available."

    def test_get_actionable_feedback(self, review_agent):
        """Test getting actionable feedback items."""
        from src.services.review_agent.review_types import ReviewResult, FeedbackItem
        
        # Create mock feedback items
        feedback_item = FeedbackItem(
            id="test_1",
            text="Add specific details"
        )
        
        mock_result = ReviewResult(
            email_content="test",
            critique="Test critique",
            actionable_feedback=[feedback_item]
        )
        
        actionable_feedback = review_agent.get_actionable_feedback(mock_result)
        assert len(actionable_feedback) == 1
        assert actionable_feedback[0].id == "test_1"

    def test_should_regenerate_email(self, review_agent):
        """Test regeneration recommendation."""
        from src.services.review_agent.review_types import ReviewResult
        
        mock_result = ReviewResult(
            email_content="test",
            critique="Test critique",
            should_regenerate=True
        )
        
        should_regenerate = review_agent.should_regenerate_email(mock_result)
        assert should_regenerate == True

    def test_get_review_display_data(self, review_agent):
        """Test getting formatted display data for UI."""
        from src.services.review_agent.review_types import ReviewResult, FeedbackItem
        
        # Create mock feedback items
        feedback_item = FeedbackItem(
            id="test_1",
            text="Add specific details about the collaboration"
        )
        
        mock_result = ReviewResult(
            email_content="test",
            critique="This email needs improvement.",
            actionable_feedback=[feedback_item],
            should_regenerate=True
        )
        
        display_data = review_agent.get_review_display_data(mock_result)
        
        assert display_data["critique"] == "This email needs improvement."
        assert display_data["should_regenerate"] == True
        assert display_data["feedback_count"] == 1
        assert len(display_data["actionable_feedback"]) == 1
        assert display_data["actionable_feedback"][0]["id"] == "test_1"
        assert display_data["actionable_feedback"][0]["text"] == "Add specific details about the collaboration"

    def test_review_email_with_all_parameters(self, review_agent, sample_email_content, sample_llm_response):
        """Test email review with all optional parameters."""
        # Mock LLM service response
        review_agent.llm_service.generate_response.return_value = sample_llm_response
        
        # Mock parser response
        from src.services.review_agent.review_types import ReviewResult
        mock_result = ReviewResult(
            email_content=sample_email_content,
            critique="Good email with template adherence.",
            should_regenerate=False
        )
        review_agent.parser.parse_review_response.return_value = mock_result
        
        template_info = {
            "industry": "healthcare",
            "forbidden_phrases": ["synergy", "leverage"],
            "writing_tips": ["Be professional", "Be concise"],
            "preferred_phrases": ["collaboration", "partnership"]
        }
        
        result = review_agent.review_email(
            email_content=sample_email_content,
            template_info=template_info,
            user_context="Healthcare outreach",
            recipient_industry="healthcare",
            extra_metadata={"urgency": "high"},
            max_tokens=2000,
            temperature=0.2
        )
        
        # Verify the prompt was built with all parameters
        call_args = review_agent.llm_service.generate_response.call_args
        prompt = call_args[1]['prompt']  # prompt is the first positional argument
        
        assert "healthcare" in prompt
        assert "synergy" in prompt
        assert "leverage" in prompt
        assert "collaboration" in prompt
        assert "partnership" in prompt
        assert "Healthcare outreach" in prompt
        assert "urgency: high" in prompt
        
        # Verify temperature and max_tokens were passed
        assert call_args[1]['temperature'] == 0.2
        assert call_args[1]['max_tokens'] == 2000 