"""
Review Agent Main Class

Orchestrates the review process: builds prompts, calls LLM, parses results, and exposes feedback.
Focuses on conversational critique with actionable feedback for UI interaction.
"""
from typing import Dict, Optional, Any, List
from .review_prompts import build_review_prompt
from .review_types import ReviewResult, FeedbackItem
from .review_parser import ReviewResponseParser
from ..llm_service import LLMService
from ...utils.error_utils import ErrorHandler
from ...utils.logging_utils import log, log_warning, log_error


class ReviewAgent:
    """
    Main Review Agent that orchestrates the email review process.
    
    Responsibilities:
    - Build review prompts requesting conversational critique
    - Call LLM service for review analysis
    - Parse LLM responses into critique and actionable feedback
    - Provide conversational critique with actionable feedback for UI
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.parser = ReviewResponseParser()

    def review_email(
        self,
        email_content: str,
        template_info: Optional[Dict] = None,
        user_context: Optional[str] = None,
        recipient_industry: Optional[str] = None,
        extra_metadata: Optional[Dict] = None,
        max_tokens: int = 1500,
        temperature: float = 0.3
    ) -> ReviewResult:
        """
        Run the complete review process on a generated email.
        
        Args:
            email_content: The email to review
            template_info: Template metadata and guidelines
            user_context: Original user request context
            recipient_industry: Target industry for tone assessment
            extra_metadata: Additional context for review
            max_tokens: Maximum tokens for LLM response
            temperature: LLM temperature for consistent parsing
            
        Returns:
            ReviewResult with conversational critique and actionable feedback
        """
        try:
            # Build the review prompt requesting conversational critique
            prompt = build_review_prompt(
                email_content=email_content,
                template_info=template_info,
                user_context=user_context,
                recipient_industry=recipient_industry,
                extra_metadata=extra_metadata
            )
            
            # Call LLM service for review analysis
            llm_response = self._call_llm_for_review(prompt, max_tokens, temperature)
            
            if not llm_response:
                log_warning("LLM returned empty response for review", prefix="ReviewAgent")
                return self._create_fallback_result(email_content, template_info, user_context)
            
            # Parse the LLM response into critique and actionable feedback
            review_result = self.parser.parse_review_response(
                llm_response=llm_response,
                email_content=email_content,
                template_info=template_info,
                user_context=user_context
            )
            
            log(f"Review completed: {len(review_result.actionable_feedback)} actionable feedback items", 
                prefix="ReviewAgent")
            
            return review_result
            
        except Exception as e:
            log_error(f"Error during email review: {str(e)}", prefix="ReviewAgent")
            return self._create_fallback_result(email_content, template_info, user_context)

    def _call_llm_for_review(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Call LLM service for review analysis with error handling."""
        def llm_call():
            return self.llm_service.generate_response(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        
        return ErrorHandler.handle_api_operation(llm_call)

    def _create_fallback_result(
        self, 
        email_content: str, 
        template_info: Optional[Dict], 
        user_context: Optional[str]
    ) -> ReviewResult:
        """Create a fallback result when LLM review fails."""
        return ReviewResult(
            email_content=email_content,
            critique="Review unavailable due to technical issues. Please check your email manually.",
            should_regenerate=False,
            template_info=template_info,
            user_context=user_context
        )

    # UI Interface Methods
    def get_critique(self, review_result: ReviewResult) -> str:
        """Get the conversational critique for UI display."""
        if not review_result.critique:
            return "No critique available."
        
        return review_result.critique

    def get_actionable_feedback(self, review_result: ReviewResult) -> List[FeedbackItem]:
        """Get actionable feedback items that can be clicked by the user in the UI."""
        return review_result.get_clickable_feedback()

    def should_regenerate_email(self, review_result: ReviewResult) -> bool:
        """Determine if the email should be regenerated based on review results."""
        return review_result.should_regenerate

    def get_review_display_data(self, review_result: ReviewResult) -> Dict[str, Any]:
        """
        Get formatted data for UI display.
        
        Returns:
            Dictionary with all data needed for UI rendering
        """
        return {
            "critique": review_result.critique,
            "actionable_feedback": [
                {
                    "id": item.id,
                    "text": item.text
                }
                for item in review_result.get_clickable_feedback()
            ],
            "should_regenerate": review_result.should_regenerate,
            "feedback_count": len(review_result.actionable_feedback)
        } 