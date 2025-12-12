"""Tests for assistant_thread_started event handler."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lsimons_bot.listeners.events.assistant_thread_started import (
    _extract_thread_data,
    assistant_thread_started_handler,
)
from lsimons_bot.slack import InvalidRequestError


class TestAssistantThreadStartedHandler:
    """Tests for assistant_thread_started_handler function."""

    @pytest.mark.asyncio
    async def test_handler_success(self) -> None:
        """Test successful thread started handler execution."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "user_id": "U123",
        }

        with patch("lsimons_bot.listeners.events.assistant_thread_started.get_channel_info") as mock_get_channel:
            with patch("lsimons_bot.listeners.events.assistant_thread_started.set_thread_status") as mock_set_status:
                with patch(
                    "lsimons_bot.listeners.events.assistant_thread_started.set_suggested_prompts"
                ) as mock_set_prompts:
                    from lsimons_bot.slack import ChannelInfo

                    mock_channel_info = ChannelInfo(
                        id="C123",
                        name="general",
                        topic="General discussion",
                        is_private=False,
                    )
                    mock_get_channel.return_value = mock_channel_info

                    await assistant_thread_started_handler(ack, body, client, test_logger)

                    ack.assert_called_once()
                    mock_set_status.assert_called_once()
                    mock_set_prompts.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_missing_thread_id(self) -> None:
        """Test handler with missing assistant_thread_id."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "channel_id": "C123",
            "user_id": "U123",
        }

        await assistant_thread_started_handler(ack, body, client, test_logger)

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
            "user_id": "U123",
        }

        await assistant_thread_started_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        test_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handler_channel_info_error(self) -> None:
        """Test handler when channel info retrieval fails."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "user_id": "U123",
        }

        with patch("lsimons_bot.listeners.events.assistant_thread_started.get_channel_info") as mock_get_channel:
            from lsimons_bot.slack import SlackChannelError

            mock_get_channel.side_effect = SlackChannelError("Channel not found")

            await assistant_thread_started_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()


class TestExtractThreadData:
    """Tests for _extract_thread_data function."""

    def test_extract_valid_data(self) -> None:
        """Test extracting valid thread data."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "user_id": "U123",
        }

        request = _extract_thread_data(body, test_logger)

        assert request.thread_id == "thread-123"
        assert request.channel_id == "C123"
        assert request.user_id == "U123"

    def test_extract_missing_thread_id(self) -> None:
        """Test extraction with missing thread_id."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "channel_id": "C123",
            "user_id": "U123",
        }

        with pytest.raises(InvalidRequestError):
            _extract_thread_data(body, test_logger)

    def test_extract_missing_channel_id(self) -> None:
        """Test extraction with missing channel_id."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "user_id": "U123",
        }

        with pytest.raises(InvalidRequestError):
            _extract_thread_data(body, test_logger)

    def test_extract_with_empty_strings(self) -> None:
        """Test extraction with empty string values."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "",
            "channel_id": "C123",
            "user_id": "U123",
        }

        with pytest.raises(InvalidRequestError):
            _extract_thread_data(body, test_logger)

    def test_extract_without_user_id(self) -> None:
        """Test extraction without user_id (optional)."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
        }

        request = _extract_thread_data(body, test_logger)

        assert request.thread_id == "thread-123"
        assert request.channel_id == "C123"
