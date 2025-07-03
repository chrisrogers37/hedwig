"""
Tests for review_prompts module.
"""
import pytest
from src.services.review_agent.review_prompts import build_review_prompt


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