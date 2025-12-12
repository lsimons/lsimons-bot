"""Tests for assistant_user_message event handler."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from listeners.events.assistant_user_message import (
    _extract_request_data,
    assistant_user_message_handler,
)
from lsimons_bot.slack import InvalidRequestError


async def async_generator(items: list[str]) -> None:
    """Helper to create async generator for mocking stream_completion."""
    for item in items:
        yield item


class TestAssistantUserMessageHandler:
    """Tests for assistant_user_message_handler function."""

    @pytest.mark.asyncio
    async def test_handler_success(self) -> None:
        """Test successful user message handler execution."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "What is machine learning?",
        }

        with patch(
            "listeners.events.assistant_user_message.get_channel_info"
        ) as mock_get_channel:
            with patch(
                "listeners.events.assistant_user_message.get_conversation_history"
            ) as mock_get_history:
                with patch(
                    "listeners.events.assistant_user_message.create_llm_client"
                ) as mock_llm:
                    mock_channel = MagicMock()
                    mock_channel.name = "general"
                    mock_channel.topic = "General discussion"
                    mock_get_channel.return_value = mock_channel

                    mock_get_history.return_value = []

                    mock_llm_client = AsyncMock()
                    mock_llm_client.stream_completion = MagicMock(
                        return_value=async_generator(["Response"])
                    )
                    mock_llm.return_value = mock_llm_client

                    with patch(
                        "listeners.events.assistant_user_message.set_thread_status"
                    ):
                        await assistant_user_message_handler(
                            ack, body, client, test_logger
                        )

                    ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_missing_thread_id(self) -> None:
        """Test handler with missing assistant_thread_id."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "channel_id": "C123",
            "text": "Hello",
        }

        await assistant_user_message_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        test_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handler_missing_channel_id(self) -> None:
        """Test handler with missing channel_id."""
        ack = AsyncMock()
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
        ack = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_handler_no_text_field(self) -> None:
        """Test handler without text field."""
        ack = AsyncMock()
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
    async def test_handler_channel_error(self) -> None:
        """Test handler when channel info retrieval fails."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        with patch(
            "listeners.events.assistant_user_message.get_channel_info"
        ) as mock_get_channel:
            from lsimons_bot.slack import SlackChannelError

            mock_get_channel.side_effect = SlackChannelError("Channel not found")

            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_llm_error(self) -> None:
        """Test handler when LLM request fails."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        with patch(
            "listeners.events.assistant_user_message.get_channel_info"
        ) as mock_get_channel:
            with patch(
                "listeners.events.assistant_user_message.get_conversation_history"
            ) as mock_get_history:
                with patch("listeners.events.assistant_user_message.set_thread_status"):
                    with patch(
                        "listeners.events.assistant_user_message.create_llm_client"
                    ) as mock_llm:
                        from lsimons_bot.slack import ChannelInfo

                        mock_channel_info = ChannelInfo(
                            id="C123",
                            name="general",
                            topic="",
                            is_private=False,
                        )
                        mock_get_channel.return_value = mock_channel_info
                        mock_get_history.return_value = []

                        mock_client = AsyncMock()
                        mock_client.stream_completion = MagicMock(
                            side_effect=Exception("LLM error")
                        )
                        mock_llm.return_value = mock_client

                        await assistant_user_message_handler(
                            ack, body, client, test_logger
                        )

                        ack.assert_called_once()
                        test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_unexpected_error(self) -> None:
        """Test handler with unexpected error."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        with patch(
            "listeners.events.assistant_user_message.get_channel_info"
        ) as mock_get_channel:
            mock_get_channel.side_effect = RuntimeError("Unexpected error")

            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()


class TestExtractRequestData:
    """Tests for _extract_request_data function."""

    def test_extract_valid_data(self) -> None:
        """Test extracting valid request data."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello assistant",
        }

        request = _extract_request_data(body, test_logger)

        assert request.thread_id == "thread-123"
        assert request.channel_id == "C123"
        assert request.user_message == "Hello assistant"

    def test_extract_missing_thread_id(self) -> None:
        """Test extraction with missing thread_id."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "channel_id": "C123",
            "text": "Hello",
        }

        with pytest.raises(InvalidRequestError):
            _extract_request_data(body, test_logger)

    def test_extract_missing_channel_id(self) -> None:
        """Test extraction with missing channel_id."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "text": "Hello",
        }

        with pytest.raises(InvalidRequestError):
            _extract_request_data(body, test_logger)

    def test_extract_empty_message(self) -> None:
        """Test extraction with empty message."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "   ",
        }

        with pytest.raises(InvalidRequestError):
            _extract_request_data(body, test_logger)

    def test_extract_missing_text_field(self) -> None:
        """Test extraction without text field."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
        }

        with pytest.raises(InvalidRequestError):
            _extract_request_data(body, test_logger)

    def test_extract_whitespace_ids(self) -> None:
        """Test extraction with whitespace-only IDs."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "   ",
            "channel_id": "C123",
            "text": "Hello",
        }

        with pytest.raises(InvalidRequestError):
            _extract_request_data(body, test_logger)
