"""
Chat History Manager for OutboundOwl

Manages conversation history including drafts, feedback, and responses.
Supports summarization for token optimization and context management.
"""

import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class MessageType(Enum):
    """Types of messages in the conversation."""
    INITIAL_PROMPT = "initial_prompt"
    DRAFT = "draft"
    FEEDBACK = "feedback"
    REVISED_DRAFT = "revised_draft"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Represents a single message in the conversation."""
    id: str
    type: MessageType
    content: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['type'] = self.type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary."""
        data['type'] = MessageType(data['type'])
        return cls(**data)


class ChatHistoryManager:
    """
    Manages conversation history with support for drafts, feedback, and summarization.
    """
    
    def __init__(self, max_history_length: int = 50, auto_summarize_threshold: int = 20):
        """
        Initialize the chat history manager.
        
        Args:
            max_history_length: Maximum number of messages to keep in memory
            auto_summarize_threshold: Number of messages before auto-summarization
        """
        self.messages: List[ChatMessage] = []
        self.max_history_length = max_history_length
        self.auto_summarize_threshold = auto_summarize_threshold
        self.summary: Optional[str] = None
        self.conversation_id: Optional[str] = None
    
    def start_conversation(self, conversation_id: Optional[str] = None) -> str:
        """
        Start a new conversation.
        
        Args:
            conversation_id: Optional custom ID, will generate one if not provided
            
        Returns:
            The conversation ID
        """
        if conversation_id is None:
            conversation_id = f"conv_{int(time.time())}_{hash(str(time.time()))}"
        
        self.conversation_id = conversation_id
        self.messages = []
        self.summary = None
        
        return conversation_id
    
    def add_message(self, 
                   content: str, 
                   message_type: MessageType, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a new message to the conversation.
        
        Args:
            content: The message content
            message_type: Type of message
            metadata: Optional metadata
            
        Returns:
            The message ID
        """
        message_id = f"msg_{int(time.time())}_{len(self.messages)}"
        
        message = ChatMessage(
            id=message_id,
            type=message_type,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        
        # Auto-summarize if we reach or exceed threshold
        if len(self.messages) >= self.auto_summarize_threshold:
            self._auto_summarize()
        
        # Trim history if we exceed max length
        if len(self.messages) > self.max_history_length:
            self._trim_history()
        
        return message_id
    
    def add_draft(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a draft message."""
        return self.add_message(content, MessageType.DRAFT, metadata)
    
    def add_feedback(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add feedback message."""
        return self.add_message(content, MessageType.FEEDBACK, metadata)
    
    def add_revised_draft(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a revised draft message."""
        return self.add_message(content, MessageType.REVISED_DRAFT, metadata)
    
    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a system message."""
        return self.add_message(content, MessageType.SYSTEM, metadata)
    
    def get_conversation_context(self, 
                                include_summary: bool = True, 
                                max_messages: Optional[int] = None) -> str:
        """
        Get the full conversation context for LLM calls.
        
        Args:
            include_summary: Whether to include the summary
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation context
        """
        context_parts = []
        
        # Add summary if available and requested
        if include_summary and self.summary:
            context_parts.append(f"CONVERSATION SUMMARY:\n{self.summary}\n")
        
        # Get messages to include
        messages_to_include = self.messages
        if max_messages:
            messages_to_include = self.messages[-max_messages:]
        
        # Format messages
        for message in messages_to_include:
            type_label = message.type.value.replace('_', ' ').title()
            context_parts.append(f"[{type_label}]: {message.content}")
        
        return "\n\n".join(context_parts)
    
    def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """Get the most recent messages."""
        return self.messages[-count:] if self.messages else []
    
    def get_messages_by_type(self, message_type: MessageType) -> List[ChatMessage]:
        """Get all messages of a specific type."""
        return [msg for msg in self.messages if msg.type == message_type]
    
    def get_latest_draft(self) -> Optional[ChatMessage]:
        """Get the most recent draft message."""
        drafts = self.get_messages_by_type(MessageType.DRAFT)
        revised_drafts = self.get_messages_by_type(MessageType.REVISED_DRAFT)
        all_drafts = drafts + revised_drafts
        return max(all_drafts, key=lambda x: x.timestamp) if all_drafts else None
    
    def get_latest_feedback(self) -> Optional[ChatMessage]:
        """Get the most recent feedback message."""
        feedbacks = self.get_messages_by_type(MessageType.FEEDBACK)
        return max(feedbacks, key=lambda x: x.timestamp) if feedbacks else None
    
    def summarize_conversation(self, llm_service=None) -> str:
        """
        Summarize the conversation using the LLM service.
        
        Args:
            llm_service: LLM service instance for summarization
            
        Returns:
            Summary of the conversation
        """
        if not self.messages:
            return "No conversation to summarize."
        
        if llm_service is None:
            # Fallback to simple summary
            return self._simple_summary()
        
        # Create summarization prompt
        conversation_text = self.get_conversation_context(include_summary=False)
        
        summary_prompt = f"""
        Please provide a concise summary of this email drafting conversation, 
        focusing on the key requirements, feedback points, and current status.
        
        Conversation:
        {conversation_text}
        
        Summary:
        """
        
        try:
            summary = llm_service.generate_response(summary_prompt)
            self.summary = summary
            return summary
        except Exception as e:
            # Fallback to simple summary
            return self._simple_summary()
    
    def _simple_summary(self) -> str:
        """Create a simple summary without LLM."""
        if not self.messages:
            return "No conversation to summarize."
        
        draft_count = len(self.get_messages_by_type(MessageType.DRAFT))
        revised_count = len(self.get_messages_by_type(MessageType.REVISED_DRAFT))
        feedback_count = len(self.get_messages_by_type(MessageType.FEEDBACK))
        
        summary = f"Conversation with {draft_count + revised_count} drafts and {feedback_count} feedback points."
        
        latest_draft = self.get_latest_draft()
        if latest_draft:
            summary += f" Latest draft created at {time.strftime('%Y-%m-%d %H:%M', time.localtime(latest_draft.timestamp))}."
        
        self.summary = summary
        return summary
    
    def _auto_summarize(self) -> None:
        """Automatically summarize the conversation."""
        if len(self.messages) >= self.auto_summarize_threshold:
            # Keep only recent messages and add summary
            keep_count = min(10, self.auto_summarize_threshold // 2)  # Keep half the threshold or 10, whichever is smaller
            recent_messages = self.messages[-keep_count:]  # Keep recent messages
            old_messages = self.messages[:-keep_count]
            
            if old_messages:  # Only summarize if there are old messages
                # Create simple summary of old messages
                draft_count = len([m for m in old_messages if m.type in [MessageType.DRAFT, MessageType.REVISED_DRAFT]])
                feedback_count = len([m for m in old_messages if m.type == MessageType.FEEDBACK])
                old_summary = f"Previous conversation had {len(old_messages)} messages with {draft_count} drafts and {feedback_count} feedback points."
                
                self.summary = old_summary
                self.messages = recent_messages
    
    def _trim_history(self) -> None:
        """Trim the message history to stay within limits."""
        if len(self.messages) > self.max_history_length:
            # Keep the most recent messages
            self.messages = self.messages[-self.max_history_length:]
    
    def export_conversation(self) -> Dict[str, Any]:
        """Export the conversation for persistence."""
        return {
            'conversation_id': self.conversation_id,
            'summary': self.summary,
            'messages': [msg.to_dict() for msg in self.messages],
            'exported_at': time.time()
        }
    
    def import_conversation(self, data: Dict[str, Any]) -> None:
        """Import a conversation from exported data."""
        self.conversation_id = data.get('conversation_id')
        self.summary = data.get('summary')
        self.messages = [ChatMessage.from_dict(msg_data) for msg_data in data.get('messages', [])]
    
    def clear_conversation(self) -> None:
        """Clear the current conversation."""
        self.messages = []
        self.summary = None
        self.conversation_id = None
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about the conversation."""
        stats = {
            'total_messages': len(self.messages),
            'drafts': len(self.get_messages_by_type(MessageType.DRAFT)),
            'revised_drafts': len(self.get_messages_by_type(MessageType.REVISED_DRAFT)),
            'feedback': len(self.get_messages_by_type(MessageType.FEEDBACK)),
            'system_messages': len(self.get_messages_by_type(MessageType.SYSTEM)),
            'has_summary': self.summary is not None,
            'conversation_id': self.conversation_id
        }
        
        if self.messages:
            stats['start_time'] = min(msg.timestamp for msg in self.messages)
            stats['end_time'] = max(msg.timestamp for msg in self.messages)
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']) / 60
        
        return stats 