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
    async def test_handler_success(self, fake_slack) -> None:
        """Test successful thread started handler execution."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "user_id": "U123",
        }

        fake_slack.with_channel(channel_id="C123", name="general", topic="General discussion")

        with (
            patch(
                "lsimons_bot.listeners.events.assistant_thread_started.get_channel_info",
                fake_slack.get_channel_info,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_thread_started.set_thread_status",
                fake_slack.set_thread_status,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_thread_started.set_suggested_prompts",
                fake_slack.set_suggested_prompts,
            ),
        ):
            await assistant_thread_started_handler(ack, body, client, test_logger)

            ack.assert_called_once()

            # Assert thread status was set with correct arguments
            status_call_args = fake_slack.set_thread_status.call_args
            assert status_call_args.args[0] == client
            assert status_call_args.args[1] == "C123"
            assert status_call_args.args[2] == "thread-123"
            assert status_call_args.args[3] == "running"

            # Assert suggested prompts was called with correct arguments
            prompts_call_args = fake_slack.set_suggested_prompts.call_args
            assert prompts_call_args.args[0] == client
            assert prompts_call_args.args[1] == "C123"
            assert prompts_call_args.args[2] == "thread-123"
            assert isinstance(prompts_call_args.args[3], list)
            assert len(prompts_call_args.args[3]) > 0

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

        # Assert warning was logged about invalid request
        log_call_args = test_logger.warning.call_args
        logged_message = log_call_args[0][0]
        assert (
            "Invalid" in logged_message
            or "invalid" in logged_message
            or "Missing" in logged_message
            or "missing" in logged_message
        )

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

        # Assert warning was logged about invalid request
        log_call_args = test_logger.warning.call_args
        logged_message = log_call_args[0][0]
        assert (
            "Invalid" in logged_message
            or "invalid" in logged_message
            or "Missing" in logged_message
            or "missing" in logged_message
        )

    @pytest.mark.asyncio
    async def test_handler_channel_info_error(self, fake_slack) -> None:
        """Test handler when channel info retrieval fails."""
        from lsimons_bot.slack import SlackChannelError

        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "user_id": "U123",
        }

        fake_slack.get_channel_info.side_effect = SlackChannelError("Channel not found")

        with patch(
            "lsimons_bot.listeners.events.assistant_thread_started.get_channel_info",
            fake_slack.get_channel_info,
        ):
            await assistant_thread_started_handler(ack, body, client, test_logger)

            ack.assert_called_once()

            # Assert error was logged about channel info failure
            log_call_args = test_logger.error.call_args
            logged_message = log_call_args[0][0]
            assert (
                "channel" in logged_message.lower()
                or "failed" in logged_message.lower()
                or "error" in logged_message.lower()
            )


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
