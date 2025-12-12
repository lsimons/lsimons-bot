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
        client.chat_postEphemeral.assert_called_once()
        test_logger.info.assert_called()

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
        client.chat_postEphemeral.assert_called_once()
        test_logger.info.assert_called()

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
        test_logger.warning.assert_called()
        client.chat_postEphemeral.assert_not_called()

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
        test_logger.warning.assert_called()
        client.chat_postEphemeral.assert_not_called()

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
        test_logger.warning.assert_called()

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
        test_logger.warning.assert_called()

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
        test_logger.warning.assert_called()

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
        client.chat_postEphemeral.assert_called_once()


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
