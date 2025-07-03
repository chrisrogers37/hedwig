"""
Simplified Review Types for Review Agent

Defines minimal data structures for email critique and actionable feedback.
Focuses on conversational critique with structured feedback items for UI interaction.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class FeedbackItem:
    """Represents a single actionable feedback item that can be clicked by the user."""
    
    id: str
    text: str  # The feedback text itself
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackItem':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            text=data["text"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
    
    def __str__(self) -> str:
        """String representation of feedback item."""
        return f"Feedback {self.id}: {self.text}"


@dataclass
class ReviewResult:
    """Complete review analysis result with minimal structure."""
    
    email_content: str
    critique: str  # The conversational critique from the LLM
    actionable_feedback: List[FeedbackItem] = field(default_factory=list)
    should_regenerate: bool = False
    template_info: Optional[Dict[str, Any]] = None
    user_context: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_feedback_item(self, feedback: FeedbackItem) -> None:
        """Add a feedback item to the result."""
        self.actionable_feedback.append(feedback)
    
    def get_clickable_feedback(self) -> List[FeedbackItem]:
        """Get feedback items that can be clicked by the user."""
        return self.actionable_feedback
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "email_content": self.email_content,
            "critique": self.critique,
            "actionable_feedback": [f.to_dict() for f in self.actionable_feedback],
            "should_regenerate": self.should_regenerate,
            "template_info": self.template_info,
            "user_context": self.user_context,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReviewResult':
        """Create from dictionary."""
        actionable_feedback = [FeedbackItem.from_dict(f) for f in data["actionable_feedback"]]
        
        return cls(
            email_content=data["email_content"],
            critique=data["critique"],
            actionable_feedback=actionable_feedback,
            should_regenerate=data["should_regenerate"],
            template_info=data.get("template_info"),
            user_context=data.get("user_context"),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
    
    def __str__(self) -> str:
        """String representation of review result."""
        return f"Review: {len(self.actionable_feedback)} feedback items, regenerate: {self.should_regenerate}"


# Helper functions for creating feedback items
def create_feedback_item(
    text: str,
    feedback_id: Optional[str] = None
) -> FeedbackItem:
    """Create a feedback item with the given text."""
    if feedback_id is None:
        feedback_id = f"feedback_{datetime.now().timestamp()}"
    
    return FeedbackItem(
        id=feedback_id,
        text=text
    ) 