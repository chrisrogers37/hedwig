"""
Integration tests for review_agent module.
"""
import pytest
from unittest.mock import Mock, patch
from src.services.review_agent.review_agent import ReviewAgent
from src.services.review_agent.review_types import ReviewResult, FeedbackItem
from src.services.llm_service import LLMService


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
        mock_result = ReviewResult(
            email_content="test",
            critique="This is a detailed critique of the email."
        )
        
        critique = review_agent.get_critique(mock_result)
        assert critique == "This is a detailed critique of the email."

    def test_get_critique_empty(self, review_agent):
        """Test getting critique when empty."""
        mock_result = ReviewResult(
            email_content="test",
            critique=""
        )
        
        critique = review_agent.get_critique(mock_result)
        assert critique == "No critique available."

    def test_get_actionable_feedback(self, review_agent):
        """Test getting actionable feedback items."""
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
        mock_result = ReviewResult(
            email_content="test",
            critique="Test critique",
            should_regenerate=True
        )
        
        should_regenerate = review_agent.should_regenerate_email(mock_result)
        assert should_regenerate == True

    def test_get_review_display_data(self, review_agent):
        """Test getting formatted display data for UI."""
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