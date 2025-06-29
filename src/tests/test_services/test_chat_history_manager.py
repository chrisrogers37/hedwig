"""
Tests for ChatHistoryManager
"""

import pytest
import time
from unittest.mock import Mock, patch
from services.chat_history_manager import (
    ChatHistoryManager, 
    ChatMessage, 
    MessageType
)


class TestChatMessage:
    """Test ChatMessage dataclass."""
    
    def test_chat_message_creation(self):
        """Test creating a ChatMessage."""
        message = ChatMessage(
            id="test_id",
            type=MessageType.DRAFT,
            content="Test content",
            timestamp=1234567890.0,
            metadata={"key": "value"}
        )
        
        assert message.id == "test_id"
        assert message.type == MessageType.DRAFT
        assert message.content == "Test content"
        assert message.timestamp == 1234567890.0
        assert message.metadata == {"key": "value"}
    
    def test_chat_message_to_dict(self):
        """Test converting ChatMessage to dictionary."""
        message = ChatMessage(
            id="test_id",
            type=MessageType.FEEDBACK,
            content="Test content",
            timestamp=1234567890.0,
            metadata={"key": "value"}
        )
        
        data = message.to_dict()
        assert data['id'] == "test_id"
        assert data['type'] == "feedback"
        assert data['content'] == "Test content"
        assert data['timestamp'] == 1234567890.0
        assert data['metadata'] == {"key": "value"}
    
    def test_chat_message_from_dict(self):
        """Test creating ChatMessage from dictionary."""
        data = {
            'id': "test_id",
            'type': "draft",
            'content': "Test content",
            'timestamp': 1234567890.0,
            'metadata': {"key": "value"}
        }
        
        message = ChatMessage.from_dict(data)
        assert message.id == "test_id"
        assert message.type == MessageType.DRAFT
        assert message.content == "Test content"
        assert message.timestamp == 1234567890.0
        assert message.metadata == {"key": "value"}


class TestChatHistoryManager:
    """Test ChatHistoryManager class."""
    
    def test_init(self):
        """Test initialization."""
        manager = ChatHistoryManager(max_history_length=100, auto_summarize_threshold=30)
        
        assert manager.messages == []
        assert manager.max_history_length == 100
        assert manager.auto_summarize_threshold == 30
        assert manager.summary is None
        assert manager.conversation_id is None
    
    def test_start_conversation(self):
        """Test starting a new conversation."""
        manager = ChatHistoryManager()
        
        # Test with custom ID
        conv_id = manager.start_conversation("custom_id")
        assert conv_id == "custom_id"
        assert manager.conversation_id == "custom_id"
        assert manager.messages == []
        assert manager.summary is None
        
        # Test with auto-generated ID
        manager.start_conversation()
        assert manager.conversation_id is not None
        assert manager.conversation_id.startswith("conv_")
    
    def test_add_message(self):
        """Test adding messages."""
        manager = ChatHistoryManager()
        manager.start_conversation("test_conv")
        
        # Add a draft message
        msg_id = manager.add_message(
            content="Test draft",
            message_type=MessageType.DRAFT,
            metadata={"tone": "professional"}
        )
        
        assert len(manager.messages) == 1
        assert manager.messages[0].content == "Test draft"
        assert manager.messages[0].type == MessageType.DRAFT
        assert manager.messages[0].metadata == {"tone": "professional"}
        assert msg_id is not None
    
    def test_add_draft(self):
        """Test adding draft messages."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        msg_id = manager.add_draft("Test draft content")
        assert len(manager.messages) == 1
        assert manager.messages[0].type == MessageType.DRAFT
        assert manager.messages[0].content == "Test draft content"
    
    def test_add_feedback(self):
        """Test adding feedback messages."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        msg_id = manager.add_feedback("Make it more concise")
        assert len(manager.messages) == 1
        assert manager.messages[0].type == MessageType.FEEDBACK
        assert manager.messages[0].content == "Make it more concise"
    
    def test_add_revised_draft(self):
        """Test adding revised draft messages."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        msg_id = manager.add_revised_draft("Revised draft content")
        assert len(manager.messages) == 1
        assert manager.messages[0].type == MessageType.REVISED_DRAFT
        assert manager.messages[0].content == "Revised draft content"
    
    def test_add_system_message(self):
        """Test adding system messages."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        msg_id = manager.add_system_message("System instruction")
        assert len(manager.messages) == 1
        assert manager.messages[0].type == MessageType.SYSTEM
        assert manager.messages[0].content == "System instruction"
    
    def test_get_conversation_context(self):
        """Test getting conversation context."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add some messages
        manager.add_draft("First draft")
        manager.add_feedback("Make it shorter")
        manager.add_revised_draft("Shorter draft")
        
        context = manager.get_conversation_context()
        
        assert "[Draft]: First draft" in context
        assert "[Feedback]: Make it shorter" in context
        assert "[Revised Draft]: Shorter draft" in context
    
    def test_get_conversation_context_with_summary(self):
        """Test getting conversation context with summary."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add a summary
        manager.summary = "Previous conversation summary"
        
        # Add a message
        manager.add_draft("Test draft")
        
        context = manager.get_conversation_context(include_summary=True)
        
        assert "CONVERSATION SUMMARY:" in context
        assert "Previous conversation summary" in context
        assert "[Draft]: Test draft" in context
    
    def test_get_conversation_context_without_summary(self):
        """Test getting conversation context without summary."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add a summary
        manager.summary = "Previous conversation summary"
        
        # Add a message
        manager.add_draft("Test draft")
        
        context = manager.get_conversation_context(include_summary=False)
        
        assert "CONVERSATION SUMMARY:" not in context
        assert "Previous conversation summary" not in context
        assert "[Draft]: Test draft" in context
    
    def test_get_conversation_context_with_max_messages(self):
        """Test getting conversation context with message limit."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add multiple messages
        manager.add_draft("First draft")
        manager.add_feedback("Feedback 1")
        manager.add_revised_draft("Second draft")
        manager.add_feedback("Feedback 2")
        
        context = manager.get_conversation_context(max_messages=2)
        
        # Should only include the last 2 messages
        assert "[Feedback]: Feedback 1" not in context
        assert "[Revised Draft]: Second draft" in context
        assert "[Feedback]: Feedback 2" in context
    
    def test_get_recent_messages(self):
        """Test getting recent messages."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add multiple messages
        manager.add_draft("First draft")
        manager.add_feedback("Feedback")
        manager.add_revised_draft("Second draft")
        
        recent = manager.get_recent_messages(count=2)
        assert len(recent) == 2
        assert recent[0].content == "Feedback"
        assert recent[1].content == "Second draft"
    
    def test_get_messages_by_type(self):
        """Test getting messages by type."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add different types of messages
        manager.add_draft("Draft 1")
        manager.add_feedback("Feedback 1")
        manager.add_draft("Draft 2")
        manager.add_feedback("Feedback 2")
        
        drafts = manager.get_messages_by_type(MessageType.DRAFT)
        feedbacks = manager.get_messages_by_type(MessageType.FEEDBACK)
        
        assert len(drafts) == 2
        assert len(feedbacks) == 2
        assert all(msg.type == MessageType.DRAFT for msg in drafts)
        assert all(msg.type == MessageType.FEEDBACK for msg in feedbacks)
    
    def test_get_latest_draft(self):
        """Test getting the latest draft."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add drafts with different timestamps
        time.sleep(0.1)  # Ensure different timestamps
        manager.add_draft("First draft")
        time.sleep(0.1)
        manager.add_revised_draft("Second draft")
        
        latest = manager.get_latest_draft()
        assert latest.content == "Second draft"
        assert latest.type == MessageType.REVISED_DRAFT
    
    def test_get_latest_feedback(self):
        """Test getting the latest feedback."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add feedback with different timestamps
        time.sleep(0.1)
        manager.add_feedback("First feedback")
        time.sleep(0.1)
        manager.add_feedback("Second feedback")
        
        latest = manager.get_latest_feedback()
        assert latest.content == "Second feedback"
    
    def test_simple_summary(self):
        """Test simple summary creation."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add some messages
        manager.add_draft("Draft 1")
        manager.add_feedback("Feedback 1")
        manager.add_revised_draft("Draft 2")
        
        summary = manager._simple_summary()
        
        assert "2 drafts" in summary
        assert "1 feedback" in summary
        assert "Latest draft created" in summary
    
    def test_simple_summary_empty_conversation(self):
        """Test simple summary with empty conversation."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        summary = manager._simple_summary()
        assert summary == "No conversation to summarize."
    
    def test_summarize_conversation_with_llm(self):
        """Test conversation summarization with LLM service."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add some messages
        manager.add_draft("First draft content")
        manager.add_feedback("Make it more professional")
        manager.add_revised_draft("Professional draft content")
        
        # Mock LLM service
        mock_llm = Mock()
        mock_llm.generate_response.return_value = "Summary: Professional email drafted with feedback incorporated."
        
        summary = manager.summarize_conversation(llm_service=mock_llm)
        
        assert summary == "Summary: Professional email drafted with feedback incorporated."
        assert manager.summary == summary
        
        # Verify LLM was called with appropriate prompt
        mock_llm.generate_response.assert_called_once()
        call_args = mock_llm.generate_response.call_args[0][0]
        assert "email drafting conversation" in call_args
        assert "First draft content" in call_args
    
    def test_summarize_conversation_without_llm(self):
        """Test conversation summarization without LLM service."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add some messages
        manager.add_draft("Draft content")
        manager.add_feedback("Feedback")
        
        summary = manager.summarize_conversation()
        
        assert "1 drafts" in summary
        assert "1 feedback" in summary
        assert manager.summary == summary
    
    def test_summarize_conversation_llm_error(self):
        """Test conversation summarization when LLM fails."""
        manager = ChatHistoryManager()
        manager.start_conversation()
        
        # Add some messages
        manager.add_draft("Draft content")
        
        # Mock LLM service that raises an exception
        mock_llm = Mock()
        mock_llm.generate_response.side_effect = Exception("LLM error")
        
        summary = manager.summarize_conversation(llm_service=mock_llm)
        
        # Should fall back to simple summary
        assert "1 drafts" in summary
        assert manager.summary == summary
    
    def test_auto_summarize(self):
        """Test automatic summarization."""
        manager = ChatHistoryManager(auto_summarize_threshold=3)
        manager.start_conversation()
        
        # Add messages up to threshold
        manager.add_draft("Draft 1")
        manager.add_feedback("Feedback 1")
        manager.add_draft("Draft 2")  # This should trigger auto-summarize
        
        # Should have summary and reduced message count
        assert manager.summary is not None
        assert len(manager.messages) <= 10  # Should keep only recent messages
    
    def test_trim_history(self):
        """Test history trimming."""
        manager = ChatHistoryManager(max_history_length=3)
        manager.start_conversation()
        
        # Add more messages than max_history_length
        manager.add_draft("Draft 1")
        manager.add_feedback("Feedback 1")
        manager.add_draft("Draft 2")
        manager.add_feedback("Feedback 2")
        manager.add_draft("Draft 3")
        manager.add_feedback("Feedback 3")
        
        # Should only keep the last 3 messages
        assert len(manager.messages) == 3
        
        # Check that we have the expected messages (the last 3 added)
        message_contents = [msg.content for msg in manager.messages]
        assert "Feedback 2" in message_contents  # 3rd from last
        assert "Draft 3" in message_contents      # 2nd from last
        assert "Feedback 3" in message_contents   # Last
    
    def test_export_conversation(self):
        """Test exporting conversation."""
        manager = ChatHistoryManager()
        manager.start_conversation("test_conv")
        manager.summary = "Test summary"
        
        # Add some messages
        manager.add_draft("Test draft")
        manager.add_feedback("Test feedback")
        
        exported = manager.export_conversation()
        
        assert exported['conversation_id'] == "test_conv"
        assert exported['summary'] == "Test summary"
        assert len(exported['messages']) == 2
        assert exported['messages'][0]['content'] == "Test draft"
        assert exported['messages'][1]['content'] == "Test feedback"
        assert 'exported_at' in exported
    
    def test_import_conversation(self):
        """Test importing conversation."""
        manager = ChatHistoryManager()
        
        # Create export data
        export_data = {
            'conversation_id': 'test_conv',
            'summary': 'Test summary',
            'messages': [
                {
                    'id': 'msg_1',
                    'type': 'draft',
                    'content': 'Test draft',
                    'timestamp': 1234567890.0,
                    'metadata': {}
                },
                {
                    'id': 'msg_2',
                    'type': 'feedback',
                    'content': 'Test feedback',
                    'timestamp': 1234567891.0,
                    'metadata': {}
                }
            ]
        }
        
        manager.import_conversation(export_data)
        
        assert manager.conversation_id == 'test_conv'
        assert manager.summary == 'Test summary'
        assert len(manager.messages) == 2
        assert manager.messages[0].content == 'Test draft'
        assert manager.messages[1].content == 'Test feedback'
    
    def test_clear_conversation(self):
        """Test clearing conversation."""
        manager = ChatHistoryManager()
        manager.start_conversation("test_conv")
        manager.summary = "Test summary"
        manager.add_draft("Test draft")
        
        manager.clear_conversation()
        
        assert manager.conversation_id is None
        assert manager.summary is None
        assert len(manager.messages) == 0
    
    def test_get_conversation_stats(self):
        """Test getting conversation statistics."""
        manager = ChatHistoryManager()
        manager.start_conversation("test_conv")
        manager.summary = "Test summary"
        
        # Add various types of messages
        manager.add_draft("Draft 1")
        manager.add_feedback("Feedback 1")
        manager.add_revised_draft("Draft 2")
        manager.add_system_message("System message")
        
        stats = manager.get_conversation_stats()
        
        assert stats['total_messages'] == 4
        assert stats['drafts'] == 1
        assert stats['revised_drafts'] == 1
        assert stats['feedback'] == 1
        assert stats['system_messages'] == 1
        assert stats['has_summary'] is True
        assert stats['conversation_id'] == "test_conv"
        assert 'start_time' in stats
        assert 'end_time' in stats
        assert 'duration_minutes' in stats
    
    def test_get_conversation_stats_empty(self):
        """Test getting conversation statistics for empty conversation."""
        manager = ChatHistoryManager()
        manager.start_conversation("test_conv")
        
        stats = manager.get_conversation_stats()
        
        assert stats['total_messages'] == 0
        assert stats['drafts'] == 0
        assert stats['revised_drafts'] == 0
        assert stats['feedback'] == 0
        assert stats['system_messages'] == 0
        assert stats['has_summary'] is False
        assert stats['conversation_id'] == "test_conv"
        assert 'start_time' not in stats
        assert 'end_time' not in stats
        assert 'duration_minutes' not in stats 