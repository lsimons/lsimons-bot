"""Unit tests for LLM context module.

Tests cover:
- Conversation history retrieval from Slack threads
- Thread context formatting
- Assistant message detection
- Error handling for failed operations
"""

from unittest.mock import MagicMock

import pytest
from slack_sdk.errors import SlackApiError

from lsimons_bot.llm.context import (
    format_thread_context,
    get_conversation_history,
    is_assistant_message,
)
from lsimons_bot.slack.exceptions import SlackThreadError


class TestGetConversationHistory:
    """Tests for conversation history retrieval."""

    def test_get_conversation_history_basic(self):
        """Get conversation history retrieves and formats messages."""
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"text": "Hello", "bot_profile": None},
                {"text": "Hi there", "bot_profile": {"id": "bot-123"}},
            ]
        }

        result = get_conversation_history(mock_client, "C123", "1234567890.000001")

        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "Hello"}
        assert result[1] == {"role": "assistant", "content": "Hi there"}

    def test_get_conversation_history_skips_subtypes(self):
        """Get conversation history skips message_changed and message_deleted."""
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"text": "Keep this", "bot_profile": None},
                {"text": "Old version", "subtype": "message_changed"},
                {"text": "Removed", "subtype": "message_deleted"},
                {"text": "Keep this too", "bot_profile": None},
            ]
        }

        result = get_conversation_history(mock_client, "C123", "1234567890.000001")

        assert len(result) == 2
        assert result[0]["content"] == "Keep this"
        assert result[1]["content"] == "Keep this too"

    def test_get_conversation_history_empty_messages(self):
        """Get conversation history handles empty text."""
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"text": "Message"},
                {"text": ""},
                {"bot_profile": None},  # No text field
            ]
        }

        result = get_conversation_history(mock_client, "C123", "1234567890.000001")

        assert len(result) == 1
        assert result[0]["content"] == "Message"

    def test_get_conversation_history_api_error(self):
        """Get conversation history raises SlackThreadError on API failure."""
        mock_client = MagicMock()
        mock_client.conversations_replies.side_effect = SlackApiError("error", "conversations.replies")

        with pytest.raises(SlackThreadError):
            get_conversation_history(mock_client, "C123", "1234567890.000001")

    def test_get_conversation_history_calls_api_correctly(self):
        """Get conversation history calls API with correct parameters."""
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {"messages": []}

        get_conversation_history(mock_client, "C123", "1234567890.000001")

        mock_client.conversations_replies.assert_called_once_with(
            channel="C123",
            ts="1234567890.000001",
        )

    def test_get_conversation_history_converts_text_to_string(self):
        """Get conversation history converts all text to strings."""
        mock_client = MagicMock()
        mock_client.conversations_replies.return_value = {
            "messages": [
                {"text": 123},  # Non-string text
                {"text": None},
            ]
        }

        result = get_conversation_history(mock_client, "C123", "1234567890.000001")

        assert len(result) == 1
        assert result[0]["content"] == "123"
        assert isinstance(result[0]["content"], str)


class TestFormatThreadContext:
    """Tests for thread context formatting."""

    def test_format_thread_context_channel_only(self):
        """Format thread context with channel name only."""
        context = format_thread_context("general")
        assert "general" in context
        assert "Channel topic:" not in context

    def test_format_thread_context_with_topic(self):
        """Format thread context includes channel topic."""
        context = format_thread_context("general", channel_topic="General discussion")
        assert "general" in context
        assert "General discussion" in context
        assert "Channel topic:" in context

    def test_format_thread_context_format(self):
        """Format thread context has proper formatting."""
        context = format_thread_context("engineering", channel_topic="Engineering team")
        assert context.startswith("You are in channel #")
        assert "#engineering" in context

    def test_format_thread_context_none_topic(self):
        """Format thread context handles None topic gracefully."""
        context = format_thread_context("design", channel_topic=None)
        assert "design" in context
        assert "Channel topic:" not in context


class TestIsAssistantMessage:
    """Tests for assistant message detection."""

    def test_is_assistant_message_with_bot_profile(self):
        """Is assistant message detects bot_profile."""
        msg = {"bot_profile": {"id": "bot-123"}}
        assert is_assistant_message(msg) is True

    def test_is_assistant_message_with_bot_id(self):
        """Is assistant message detects bot_id."""
        msg = {"bot_id": "B123456"}
        assert is_assistant_message(msg) is True

    def test_is_assistant_message_with_subtype(self):
        """Is assistant message detects bot_message subtype."""
        msg = {"subtype": "bot_message"}
        assert is_assistant_message(msg) is True

    def test_is_assistant_message_user_message(self):
        """Is assistant message returns False for user messages."""
        msg = {"text": "Hello", "user": "U123"}
        assert is_assistant_message(msg) is False

    def test_is_assistant_message_no_indicators(self):
        """Is assistant message returns False with no bot indicators."""
        msg = {"text": "Regular message"}
        assert is_assistant_message(msg) is False

    def test_is_assistant_message_empty_dict(self):
        """Is assistant message returns False for empty message."""
        msg = {}
        assert is_assistant_message(msg) is False

    def test_is_assistant_message_none_bot_profile(self):
        """Is assistant message handles None bot_profile."""
        msg = {"bot_profile": None}
        assert is_assistant_message(msg) is False

    def test_is_assistant_message_all_checks(self):
        """Is assistant message checks all indicators."""
        msg = {
            "bot_profile": {"id": "bot-123"},
            "bot_id": "B123",
            "subtype": "bot_message",
        }
        assert is_assistant_message(msg) is True
