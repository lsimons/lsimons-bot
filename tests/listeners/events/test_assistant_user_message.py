"""Tests for assistant_user_message event handler."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lsimons_bot.listeners.events.assistant_user_message import (
    _extract_request_data,
    assistant_user_message_handler,
)
from lsimons_bot.slack import InvalidRequestError


class TestAssistantUserMessageHandler:
    """Tests for assistant_user_message_handler function."""

    @pytest.mark.asyncio
    async def test_handler_success(self, fake_slack, fake_llm) -> None:
        """Test successful user message handler execution."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "What is machine learning?",
        }

        fake_slack.with_channel(name="general", topic="General discussion")
        fake_llm.with_streaming_response(["Response"])

        with (
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_channel_info",
                fake_slack.get_channel_info,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_conversation_history",
                fake_slack.get_conversation_history,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.create_llm_client",
                fake_llm.create_llm_client,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.set_thread_status",
                fake_slack.set_thread_status,
            ),
        ):
            await assistant_user_message_handler(ack, body, client, test_logger)

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
    async def test_handler_channel_error(self, fake_slack) -> None:
        """Test handler when channel info retrieval fails."""
        from lsimons_bot.slack import SlackChannelError

        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        fake_slack.get_channel_info.side_effect = SlackChannelError("Channel not found")

        with patch(
            "lsimons_bot.listeners.events.assistant_user_message.get_channel_info",
            fake_slack.get_channel_info,
        ):
            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_llm_error(self, fake_slack, fake_llm) -> None:
        """Test handler when LLM request fails."""
        from lsimons_bot.llm.exceptions import LLMAPIError

        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        fake_slack.with_channel(channel_id="C123", name="general", topic="")
        fake_llm.with_error(LLMAPIError("LLM error"))

        with (
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_channel_info",
                fake_slack.get_channel_info,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_conversation_history",
                fake_slack.get_conversation_history,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.create_llm_client",
                fake_llm.create_llm_client,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.set_thread_status",
                fake_slack.set_thread_status,
            ),
        ):
            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_slack_channel_error_in_processing(self, fake_slack) -> None:
        """Test handler when SlackChannelError occurs during processing."""
        from lsimons_bot.slack import SlackChannelError

        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        fake_slack.get_channel_info.side_effect = SlackChannelError("Channel not found")

        with patch(
            "lsimons_bot.listeners.events.assistant_user_message.get_channel_info",
            fake_slack.get_channel_info,
        ):
            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_slack_thread_error(self, fake_slack) -> None:
        """Test handler when SlackThreadError occurs during processing."""
        from lsimons_bot.slack import SlackThreadError

        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        fake_slack.with_channel(channel_id="C123", name="general", topic="")
        fake_slack.set_thread_status.side_effect = SlackThreadError("Thread not found")

        with (
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_channel_info",
                fake_slack.get_channel_info,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_conversation_history",
                fake_slack.get_conversation_history,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.set_thread_status",
                fake_slack.set_thread_status,
            ),
        ):
            await assistant_user_message_handler(ack, body, client, test_logger)

            ack.assert_called_once()
            test_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handler_llm_configuration_error(self, fake_slack, fake_llm) -> None:
        """Test handler when LLM configuration error occurs."""
        from lsimons_bot.llm.exceptions import LLMConfigurationError

        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
            "text": "Hello",
        }

        fake_slack.with_channel(channel_id="C123", name="general", topic="")
        fake_llm.with_error(LLMConfigurationError("Missing API key"))

        with (
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_channel_info",
                fake_slack.get_channel_info,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.get_conversation_history",
                fake_slack.get_conversation_history,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.create_llm_client",
                fake_llm.create_llm_client,
            ),
            patch(
                "lsimons_bot.listeners.events.assistant_user_message.set_thread_status",
                fake_slack.set_thread_status,
            ),
        ):
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


class TestSendErrorToUser:
    """Tests for _send_error_to_user function."""

    @pytest.mark.asyncio
    async def test_send_error_to_user_success(self, fake_slack) -> None:
        """Test sending error message to user successfully."""
        from lsimons_bot.listeners.events.assistant_user_message import (
            _send_error_to_user,
        )

        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
        }

        with patch(
            "lsimons_bot.listeners.events.assistant_user_message.set_thread_status",
            fake_slack.set_thread_status,
        ):
            await _send_error_to_user(client, body, "Error message", test_logger)

            fake_slack.set_thread_status.assert_called_once_with(client, "C123", "thread-123", "waiting_on_user")

    @pytest.mark.asyncio
    async def test_send_error_to_user_missing_thread_id(self) -> None:
        """Test sending error when thread_id is missing."""
        from lsimons_bot.listeners.events.assistant_user_message import (
            _send_error_to_user,
        )

        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "channel_id": "C123",
        }

        await _send_error_to_user(client, body, "Error message", test_logger)

        test_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_send_error_to_user_missing_channel_id(self) -> None:
        """Test sending error when channel_id is missing."""
        from lsimons_bot.listeners.events.assistant_user_message import (
            _send_error_to_user,
        )

        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
        }

        await _send_error_to_user(client, body, "Error message", test_logger)

        test_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_send_error_to_user_slack_error(self, fake_slack) -> None:
        """Test sending error when Slack API fails."""
        from lsimons_bot.listeners.events.assistant_user_message import (
            _send_error_to_user,
        )
        from lsimons_bot.slack import SlackThreadError

        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "assistant_thread_id": "thread-123",
            "channel_id": "C123",
        }

        fake_slack.set_thread_status.side_effect = SlackThreadError("Thread not found")

        with patch(
            "lsimons_bot.listeners.events.assistant_user_message.set_thread_status",
            fake_slack.set_thread_status,
        ):
            await _send_error_to_user(client, body, "Error message", test_logger)

            test_logger.warning.assert_called()
