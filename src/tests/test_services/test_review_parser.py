"""
Tests for review_parser module.
"""
import pytest
from src.services.review_agent.review_parser import ReviewResponseParser
from src.services.review_agent.review_types import FeedbackItem


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
         - Make the subject line more compelling
        
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
        assert len(feedback_items) == 4
        assert feedback_items[0].text.startswith("Add specific details")
        assert feedback_items[1].text.startswith("Include more personalization")
        assert feedback_items[2].text.startswith("Consider adding a clear call")
        assert feedback_items[3].text.startswith("Make the subject line")

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
        assert len(result.actionable_feedback) == 4
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
        assert result.critique == llm_response 