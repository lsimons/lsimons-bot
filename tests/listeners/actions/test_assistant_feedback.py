"""Tests for assistant_feedback action handler."""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from slack_sdk.errors import SlackApiError

from lsimons_bot.listeners.actions.assistant_feedback import (
    FeedbackRequest,
    _extract_feedback_data,
    _log_feedback,
    assistant_feedback_handler,
)
from lsimons_bot.slack import InvalidRequestError


class TestAssistantFeedbackHandler:
    """Tests for assistant_feedback_handler function."""

    @pytest.mark.asyncio
    async def test_handler_thumbs_up(self) -> None:
        """Test handling thumbs up feedback."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_up"}],
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
            "team": {"id": "T123"},
        }

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()

        # Assert the ephemeral message was sent with correct parameters
        call_args = client.chat_postEphemeral.call_args
        assert call_args.kwargs["channel"] == "C123"
        assert call_args.kwargs["user"] == "U123"
        assert call_args.kwargs["thread_ts"] == "1234567890.123456"
        assert "Thank you" in call_args.kwargs["text"]

        # Assert feedback was logged with correct event name
        # Check that "feedback_event" appears in one of the logger.info calls
        info_calls = [call[0][0] for call in test_logger.info.call_args_list]
        assert "feedback_event" in info_calls

    @pytest.mark.asyncio
    async def test_handler_thumbs_down(self) -> None:
        """Test handling thumbs down feedback."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_down"}],
            "user": {"id": "U456"},
            "channel": {"id": "C456"},
            "message": {"ts": "1234567891.123456"},
            "team": {"id": "T123"},
        }

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()

        # Assert the ephemeral message was sent with correct parameters
        call_args = client.chat_postEphemeral.call_args
        assert call_args.kwargs["channel"] == "C456"
        assert call_args.kwargs["user"] == "U456"
        assert call_args.kwargs["thread_ts"] == "1234567891.123456"
        assert "Thank you" in call_args.kwargs["text"]

        # Assert feedback was logged with correct event name
        # Check that "feedback_event" appears in one of the logger.info calls
        info_calls = [call[0][0] for call in test_logger.info.call_args_list]
        assert "feedback_event" in info_calls

    @pytest.mark.asyncio
    async def test_handler_missing_action_value(self) -> None:
        """Test handler with missing action value."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{}],
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
            "team": {"id": "T123"},
        }

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        client.chat_postEphemeral.assert_not_called()

        # Assert warning was logged with details about the invalid request
        log_call_args = test_logger.warning.call_args
        assert "Invalid" in log_call_args[0][0] or "invalid" in log_call_args[0][0]

    @pytest.mark.asyncio
    async def test_handler_missing_user_id(self) -> None:
        """Test handler with missing user_id."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_up"}],
            "user": {},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
            "team": {"id": "T123"},
        }

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()
        client.chat_postEphemeral.assert_not_called()

        # Assert warning was logged with details about the invalid request
        log_call_args = test_logger.warning.call_args
        assert "Invalid" in log_call_args[0][0] or "invalid" in log_call_args[0][0]

    @pytest.mark.asyncio
    async def test_handler_missing_actions_array(self) -> None:
        """Test handler with missing actions array."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
            "team": {"id": "T123"},
        }

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()

        # Assert warning was logged with details about the invalid request
        log_call_args = test_logger.warning.call_args
        assert "Invalid" in log_call_args[0][0] or "invalid" in log_call_args[0][0]

    @pytest.mark.asyncio
    async def test_handler_ephemeral_message_failure(self) -> None:
        """Test handler when sending ephemeral message fails."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_up"}],
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
            "team": {"id": "T123"},
        }

        client.chat_postEphemeral.side_effect = SlackApiError(
            message="channel_not_found",
            response={"error": "channel_not_found"},
        )

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()

        # Assert warning was logged about the Slack API error
        log_call_args = test_logger.warning.call_args
        logged_message = log_call_args[0][0]
        assert (
            "channel_not_found" in logged_message
            or "Slack" in logged_message
            or "Failed" in logged_message
            or "failed" in logged_message
        )

    @pytest.mark.asyncio
    async def test_handler_unexpected_error(self) -> None:
        """Test handler with unexpected error from Slack API."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_up"}],
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
            "team": {"id": "T123"},
        }

        client.chat_postEphemeral.side_effect = SlackApiError(
            message="api_error",
            response={"error": "api_error"},
        )

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()

        # Assert warning was logged about the Slack API error
        log_call_args = test_logger.warning.call_args
        logged_message = log_call_args[0][0]
        assert (
            "api_error" in logged_message
            or "Slack" in logged_message
            or "Failed" in logged_message
            or "failed" in logged_message
        )

    @pytest.mark.asyncio
    async def test_handler_without_optional_fields(self) -> None:
        """Test handler without optional fields like team_id."""
        ack = AsyncMock()
        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_up"}],
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
        }

        await assistant_feedback_handler(ack, body, client, test_logger)

        ack.assert_called_once()

        # Assert the ephemeral message was sent with correct required parameters
        call_args = client.chat_postEphemeral.call_args
        assert call_args.kwargs["channel"] == "C123"
        assert call_args.kwargs["user"] == "U123"
        assert call_args.kwargs["thread_ts"] == "1234567890.123456"


class TestExtractFeedbackData:
    """Tests for _extract_feedback_data function."""

    def test_extract_positive_feedback(self) -> None:
        """Test extracting positive feedback data."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_up"}],
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
            "team": {"id": "T123"},
        }

        request = _extract_feedback_data(body, test_logger)

        assert request.feedback_type == "positive"
        assert request.user_id == "U123"
        assert request.channel_id == "C123"
        assert request.response_ts == "1234567890.123456"

    def test_extract_negative_feedback(self) -> None:
        """Test extracting negative feedback data."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_down"}],
            "user": {"id": "U456"},
            "channel": {"id": "C456"},
            "message": {"ts": "1234567891.123456"},
            "team": {"id": "T456"},
        }

        request = _extract_feedback_data(body, test_logger)

        assert request.feedback_type == "negative"
        assert request.user_id == "U456"

    def test_extract_missing_action_raises_error(self) -> None:
        """Test that missing action value raises InvalidRequestError."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{}],
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
        }

        with pytest.raises(InvalidRequestError):
            _extract_feedback_data(body, test_logger)

    def test_extract_missing_user_id_raises_error(self) -> None:
        """Test that missing user_id raises InvalidRequestError."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "actions": [{"value": "feedback_thumbs_up"}],
            "user": {},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
        }

        with pytest.raises(InvalidRequestError):
            _extract_feedback_data(body, test_logger)

    def test_extract_missing_actions_raises_error(self) -> None:
        """Test that missing actions array raises InvalidRequestError."""
        test_logger = MagicMock(spec=logging.Logger)

        body = {
            "user": {"id": "U123"},
            "channel": {"id": "C123"},
            "message": {"ts": "1234567890.123456"},
        }

        with pytest.raises(InvalidRequestError):
            _extract_feedback_data(body, test_logger)


class TestLogFeedback:
    """Tests for _log_feedback function."""

    def test_log_feedback_positive(self) -> None:
        """Test logging positive feedback."""
        test_logger = MagicMock(spec=logging.Logger)

        request = FeedbackRequest(
            feedback_type="positive",
            user_id="U123",
            channel_id="C123",
            response_ts="1234567890.123456",
            team_id="T123",
        )

        _log_feedback(request, test_logger)

        test_logger.info.assert_called_once()
        call_args = test_logger.info.call_args
        assert call_args[0][0] == "feedback_event"

    def test_log_feedback_negative(self) -> None:
        """Test logging negative feedback."""
        test_logger = MagicMock(spec=logging.Logger)

        request = FeedbackRequest(
            feedback_type="negative",
            user_id="U456",
            channel_id="C456",
            response_ts="1234567891.123456",
            team_id="T456",
        )

        _log_feedback(request, test_logger)

        test_logger.info.assert_called_once()

    def test_log_feedback_with_none_values(self) -> None:
        """Test logging feedback with None values."""
        test_logger = MagicMock(spec=logging.Logger)

        request = FeedbackRequest(
            feedback_type="positive",
            user_id="U123",
            channel_id=None,
            response_ts=None,
            team_id=None,
        )

        _log_feedback(request, test_logger)

        test_logger.info.assert_called_once()


class TestSafeAckFunction:
    """Tests for safe_ack function."""

    @pytest.mark.asyncio
    async def test_safe_ack_with_async_callable(self) -> None:
        """Test safe_ack with async callable that returns awaitable."""
        from lsimons_bot.listeners.utils import safe_ack

        ack = AsyncMock()
        await safe_ack(ack)

        ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_ack_with_sync_callable(self) -> None:
        """Test safe_ack with sync callable that returns non-awaitable."""
        from lsimons_bot.listeners.utils import safe_ack

        def ack_sync() -> None:
            pass

        await safe_ack(ack_sync)
        # Should not raise, just return

    @pytest.mark.asyncio
    async def test_safe_ack_with_awaitable_result(self) -> None:
        """Test safe_ack when ack returns an awaitable."""
        from lsimons_bot.listeners.utils import safe_ack

        async def ack_async_returns_coroutine() -> None:
            pass

        # Call the async function to get a coroutine (awaitable)
        coro = ack_async_returns_coroutine()

        def ack_that_returns_awaitable() -> object:
            return coro

        await safe_ack(ack_that_returns_awaitable)
        # Should await the result successfully

    @pytest.mark.asyncio
    async def test_safe_ack_with_type_error(self) -> None:
        """Test safe_ack when ack raises TypeError."""
        from lsimons_bot.listeners.utils import safe_ack

        def ack_that_raises() -> None:
            raise TypeError("ack requires arguments")

        await safe_ack(ack_that_raises)
        # Should not raise, just return


class TestSendAcknowledgmentFunction:
    """Tests for _send_acknowledgment function."""

    @pytest.mark.asyncio
    async def test_send_acknowledgment_missing_channel_and_response_ts(self) -> None:
        """Test _send_acknowledgment when channel_id and response_ts are missing."""
        from lsimons_bot.listeners.actions.assistant_feedback import (
            _send_acknowledgment,
        )

        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        request = FeedbackRequest(
            feedback_type="positive",
            user_id="U123",
            channel_id=None,
            response_ts=None,
            team_id="T123",
        )

        await _send_acknowledgment(request, client, test_logger)

        client.chat_postEphemeral.assert_not_called()

        # Assert warning was logged about missing required fields
        log_call_args = test_logger.warning.call_args
        logged_message = log_call_args[0][0]
        assert "channel" in logged_message.lower() or "missing" in logged_message.lower()

    @pytest.mark.asyncio
    async def test_send_acknowledgment_missing_response_ts(self) -> None:
        """Test _send_acknowledgment when response_ts is missing."""
        from lsimons_bot.listeners.actions.assistant_feedback import (
            _send_acknowledgment,
        )

        client = MagicMock()
        test_logger = MagicMock(spec=logging.Logger)

        request = FeedbackRequest(
            feedback_type="positive",
            user_id="U123",
            channel_id="C123",
            response_ts=None,
            team_id="T123",
        )

        await _send_acknowledgment(request, client, test_logger)

        client.chat_postEphemeral.assert_not_called()

        # Assert warning was logged about missing required fields
        log_call_args = test_logger.warning.call_args
        logged_message = log_call_args[0][0]
        assert "response_ts" in logged_message or "thread" in logged_message.lower() or "missing" in logged_message.lower()
