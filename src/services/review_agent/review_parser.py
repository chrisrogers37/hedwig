"""
Simplified Review Response Parser

Parses LLM review responses to extract critique and actionable feedback.
Focuses on conversational critique with minimal structure for UI interaction.
"""
import re
from typing import Dict, Optional, List, Any
from .review_types import ReviewResult, FeedbackItem
from ...utils.logging_utils import log


class ReviewResponseParser:
    """
    Simplified parser for LLM review responses.
    
    Responsibilities:
    - Extract conversational critique
    - Extract actionable feedback items for UI
    - Determine if email should be regenerated
    - Preserve the nuanced LLM critique
    """
    
    def __init__(self):
        # Simple patterns for structured sections
        self.critique_pattern = re.compile(r'## CRITIQUE\s*\n(.*?)(?=\n## |$)', re.IGNORECASE | re.DOTALL)
        self.feedback_pattern = re.compile(r'## FEEDBACK\s*\n(.*?)(?=\n## |$)', re.IGNORECASE | re.DOTALL)
        self.recommendation_pattern = re.compile(r'## RECOMMENDATION\s*\n(KEEP|REGENERATE)', re.IGNORECASE)
        
    def parse_review_response(
        self,
        llm_response: str,
        email_content: str,
        template_info: Optional[Dict] = None,
        user_context: Optional[str] = None
    ) -> ReviewResult:
        """
        Parse LLM response into a structured ReviewResult with minimal structure.
        
        Args:
            llm_response: Raw LLM response text
            email_content: Original email content being reviewed
            template_info: Template metadata for context
            user_context: User request context
            
        Returns:
            ReviewResult with critique and actionable feedback
        """
        try:
            # Create base result
            result = ReviewResult(
                email_content=email_content,
                critique="",
                template_info=template_info,
                user_context=user_context
            )
            
            # Extract critique (the main conversational feedback)
            critique = self._extract_critique(llm_response)
            result.critique = critique
            
            # Extract actionable feedback items
            feedback_items = self._extract_actionable_feedback(llm_response)
            for item in feedback_items:
                result.add_feedback_item(item)
            
            # Determine if email should be regenerated
            should_regenerate = self._should_regenerate(llm_response)
            result.should_regenerate = should_regenerate
            
            log(f"Parsed review: {len(feedback_items)} actionable feedback items, "
                f"regenerate: {should_regenerate}", prefix="ReviewParser")
            
            return result
            
        except Exception as e:
            log(f"Error parsing review response: {str(e)}", prefix="ReviewParser", level="ERROR")
            return self._create_fallback_result(email_content, template_info, user_context, llm_response)

    def _extract_critique(self, llm_response: str) -> str:
        """Extract the conversational critique section."""
        critique_match = self.critique_pattern.search(llm_response)
        if critique_match:
            critique = critique_match.group(1).strip()
            return critique
        
        # Fallback: take the first substantial paragraph that's not feedback or recommendation
        lines = llm_response.strip().split('\n')
        critique_lines = []
        
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith(('##', 'ACTIONABLE FEEDBACK', 'RECOMMENDATION')) and
                not line.startswith('•') and  # Skip bullet points
                len(line) > 20):  # Substantial line
                critique_lines.append(line)
                if len(critique_lines) >= 3:  # Take first 3 substantial lines
                    break
        
        critique = ' '.join(critique_lines)
        return critique if critique else "Review completed successfully."

    def _extract_actionable_feedback(self, llm_response: str) -> List[FeedbackItem]:
        """Extract actionable feedback items from the structured response."""
        feedback_items = []
        
        # Extract the actionable feedback section
        feedback_match = self.feedback_pattern.search(llm_response)
        if feedback_match:
            feedback_text = feedback_match.group(1).strip()
            items = self._split_feedback_items(feedback_text)
            
            for i, item_text in enumerate(items):
                feedback_item = self._create_feedback_item(item_text, i)
                if feedback_item:
                    feedback_items.append(feedback_item)
        
        return feedback_items

    def _split_feedback_items(self, feedback_text: str) -> List[str]:
        """Split feedback text into individual actionable items, capturing multi-line bullets as a single item."""
        # Regex to match bullets (•, -, *, or numbered) at the start of a line, capturing following lines until the next bullet or end
        bullet_regex = re.compile(r'^(?:\s*[-•*]|\s*\d+\.)\s+(.*?)(?=^\s*[-•*]|^\s*\d+\.|\Z)', re.MULTILINE | re.DOTALL)
        items = [m.strip() for m in bullet_regex.findall(feedback_text)]
        # Filter out empty or too-short items, and section headers
        cleaned_items = [item for item in items if item and len(item) > 10 and not item.startswith('## ')]
        return cleaned_items[:5]  # Limit to 5 items

    def _create_feedback_item(self, item_text: str, index: int) -> Optional[FeedbackItem]:
        """Create a feedback item from actionable feedback text."""
        try:
            feedback_item = FeedbackItem(
                id=f"feedback_{index}",
                text=item_text.strip()
            )
            return feedback_item
        except Exception as e:
            log(f"Error creating feedback item: {str(e)}", prefix="ReviewParser", level="WARNING")
            return None

    def _should_regenerate(self, llm_response: str) -> bool:
        """Determine if email should be regenerated based on recommendation."""
        # Check explicit recommendation
        recommendation_match = self.recommendation_pattern.search(llm_response)
        if recommendation_match:
            recommendation = recommendation_match.group(1).upper()
            return recommendation == "REGENERATE"
        
        # Fallback: check for regeneration keywords
        response_lower = llm_response.lower()
        regenerate_keywords = ['regenerate', 'rewrite', 'start over', 'try again', 'needs significant improvement']
        if any(keyword in response_lower for keyword in regenerate_keywords):
            return True
        
        # Default to keep
        return False

    def _create_fallback_result(
        self, 
        email_content: str, 
        template_info: Optional[Dict], 
        user_context: Optional[str],
        llm_response: str
    ) -> ReviewResult:
        """Create a fallback result when parsing fails."""
        return ReviewResult(
            email_content=email_content,
            critique=f"Review completed but parsing failed. Raw response: {llm_response[:200]}...",
            should_regenerate=False,
            template_info=template_info,
            user_context=user_context
        ) 