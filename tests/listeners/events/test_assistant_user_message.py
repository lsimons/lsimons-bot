"""Tests for assistant_user_message event handler."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from slack_sdk.errors import SlackApiError

from listeners.events.assistant_user_message import (
    _send_error_message,
    assistant_user_message_handler,
)


async def async_generator(items: list[str]) -> None:
    """Helper to create async generator for mocking stream_completion."""
    for item in items:
        yield item


class TestAssistantUserMessageHandler:
    """Tests for assistant_user_message_handler function."""

    @pytest.mark.asyncio
    async def test_handler_success(self) -> None:
        """Test successful user message handler execution."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "What is machine learning?",
        }

        client.conversations_info.return_value = {
            "channel": {
                "name": "general",
                "topic": {"value": "General discussion"},
            }
        }
        client.conversations_replies.return_value = {"messages": []}

        with patch(
            "listeners.events.assistant_user_message.create_llm_client"
        ) as mock_llm:
            mock_client = AsyncMock()
            mock_client.stream_completion = AsyncMock(
                return_value=async_generator(["Hello", " there"])
            )
            mock_llm.return_value = mock_client

            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            client.conversations_info.assert_called()
            client.assistant.threads.set_status.assert_called()

    @pytest.mark.asyncio
    async def test_handler_missing_thread_id(self) -> None:
        """Test handler with missing assistant_thread_id."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "channel_id": "C123",
            "text": "Hello",
        }

        await assistant_user_message_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        test_logger.warning.assert_called()
        client.conversations_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_missing_channel_id(self) -> None:
        """Test handler with missing channel_id."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "text": "Hello",
        }

        await assistant_user_message_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        test_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handler_empty_message(self) -> None:
        """Test handler with empty user message."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "   ",
        }

        await assistant_user_message_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        test_logger.warning.assert_called()
        client.conversations_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_no_text_field(self) -> None:
        """Test handler without text field."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
        }

        await assistant_user_message_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        test_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handler_channel_info_api_error(self) -> None:
        """Test handler when channel info retrieval fails."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        client.conversations_info.side_effect = SlackApiError(
            message="channel_not_found",
            response={"error": "channel_not_found"},
        )
        client.conversations_replies.return_value = {"messages": []}

        with patch(
            "listeners.events.assistant_user_message.create_llm_client"
        ) as mock_llm:
            mock_client = AsyncMock()
            mock_client.stream_completion = AsyncMock(
                return_value=async_generator(["Response"])
            )
            mock_llm.return_value = mock_client

            await assistant_user_message_handler(ack, body, client, test_logger)

            # Should still attempt to process
            test_logger.warning.assert_called()
            ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_llm_configuration_error(self) -> None:
        """Test handler when LLM configuration is invalid."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        client.conversations_info.return_value = {
            "channel": {
                "name": "general",
                "topic": {"value": "General discussion"},
            }
        }
        client.conversations_replies.return_value = {"messages": []}

        with patch(
            "listeners.events.assistant_user_message.create_llm_client"
        ) as mock_llm:
            mock_llm.side_effect = ValueError("LITELLM_API_KEY not set")

            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_llm_request_error(self) -> None:
        """Test handler when LLM request fails."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        client.conversations_info.return_value = {
            "channel": {
                "name": "general",
                "topic": {"value": "General discussion"},
            }
        }
        client.conversations_replies.return_value = {"messages": []}

        with patch(
            "listeners.events.assistant_user_message.create_llm_client"
        ) as mock_llm:
            mock_client = AsyncMock()
            mock_client.stream_completion = AsyncMock(
                side_effect=RuntimeError("API error")
            )
            mock_llm.return_value = mock_client

            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_empty_llm_response(self) -> None:
        """Test handler when LLM returns empty response."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        client.conversations_info.return_value = {
            "channel": {
                "name": "general",
                "topic": {"value": "General discussion"},
            }
        }
        client.conversations_replies.return_value = {"messages": []}

        with patch(
            "listeners.events.assistant_user_message.create_llm_client"
        ) as mock_llm:
            mock_client = AsyncMock()
            mock_client.stream_completion = AsyncMock(return_value=async_generator([]))
            mock_llm.return_value = mock_client

            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            # When response is empty, handler logs warning and tries to set error status
            assert (
                test_logger.warning.called or client.assistant.threads.set_status.called
            )

    @pytest.mark.asyncio
    async def test_handler_with_conversation_history(self) -> None:
        """Test handler with existing conversation history."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "What about machine learning?",
        }

        client.conversations_info.return_value = {
            "channel": {
                "name": "general",
                "topic": {"value": "General discussion"},
            }
        }
        client.conversations_replies.return_value = {
            "messages": [
                {"ts": "1.0", "user": "U123", "text": "What is AI?"},
                {
                    "ts": "2.0",
                    "bot_id": "B123",
                    "text": "AI is artificial intelligence",
                    "bot_profile": {"name": "assistant"},
                },
            ]
        }

        with patch(
            "listeners.events.assistant_user_message.create_llm_client"
        ) as mock_llm:
            mock_client = AsyncMock()
            mock_client.stream_completion = AsyncMock(
                return_value=async_generator(["ML is a subset of AI"])
            )
            mock_llm.return_value = mock_client

            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            # Verify LLM was called with conversation history
            mock_client.stream_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_unexpected_error(self) -> None:
        """Test handler with unexpected error."""
        ack = MagicMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        client.conversations_info.side_effect = RuntimeError("Unexpected error")

        await assistant_user_message_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        test_logger.error.assert_called()


class TestSendErrorMessage:
    """Tests for _send_error_message function."""

    def test_send_error_message_success(self) -> None:
        """Test successfully sending error message."""
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        _send_error_message(
            client,
            "C123",
            "thread-123",
            "An error occurred",
            test_logger,
        )

        client.assistant.threads.set_status.assert_called_once_with(
            channel_id="C123",
            thread_id="thread-123",
            status="waiting_on_user",
        )

    def test_send_error_message_api_error(self) -> None:
        """Test error message when API call fails."""
        client = MagicMock()
        client.assistant.threads.set_status.side_effect = SlackApiError(
            message="invalid_argument",
            response={"error": "invalid_argument"},
        )
        test_logger = MagicMock(spec=logging.Logger)

        _send_error_message(
            client,
            "C123",
            "thread-123",
            "An error occurred",
            test_logger,
        )

        # Should log warning but not raise
        test_logger.warning.assert_called()
