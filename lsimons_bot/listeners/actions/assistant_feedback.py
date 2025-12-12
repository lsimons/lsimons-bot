"""Handler for assistant feedback actions.

Triggered when users click thumbs up/down buttons on assistant responses.
Logs feedback and sends acknowledgment to user.

This version:
- Calls `ack` in a way that supports both sync and async ack callables.
- Uses precise typing (avoids `Any` where possible).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Mapping, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from lsimons_bot.listeners.utils import safe_ack
from lsimons_bot.slack import InvalidRequestError

logger = logging.getLogger(__name__)


@dataclass
class FeedbackRequest:
    """Validated feedback action data."""

    feedback_type: str  # "positive" or "negative"
    user_id: str
    channel_id: Optional[str]
    response_ts: Optional[str]
    team_id: Optional[str]


def _extract_feedback_data(
    body: Mapping[str, object],
    logger_: logging.Logger,
) -> FeedbackRequest:
    """Extract and validate feedback action data.

    Args:
        body: Action payload
        logger_: Logger instance

    Returns:
        Validated FeedbackRequest

    Raises:
        InvalidRequestError: If required fields are missing or malformed
    """
    # actions is expected to be a sequence of dict-like items
    actions = body.get("actions")
    if not actions or not isinstance(actions, (list, tuple)):
        logger_.warning("No actions in feedback payload")
        raise InvalidRequestError("No actions in feedback payload")

    first_action = actions[0]
    if not isinstance(first_action, Mapping):
        logger_.warning("Invalid action shape")
        raise InvalidRequestError("Invalid action payload")

    action_value = str(first_action.get("value", "")).strip()
    user = body.get("user", {})
    user_id = ""
    if isinstance(user, Mapping):
        user_id = str(user.get("id", "") or "").strip()

    channel = body.get("channel", {})
    channel_id = None
    if isinstance(channel, Mapping):
        channel_id = channel.get("id")  # may be None

    message = body.get("message", {})
    response_ts = None
    if isinstance(message, Mapping):
        response_ts = message.get("ts")

    team = body.get("team", {})
    team_id = None
    if isinstance(team, Mapping):
        team_id = team.get("id")

    if not action_value or not user_id:
        logger_.warning("Missing required fields: action_value or user_id")
        raise InvalidRequestError("Missing required fields: action_value or user_id")

    feedback_type = "positive" if action_value == "feedback_thumbs_up" else "negative"

    logger_.info(
        "Received feedback: type=%s, user=%s, channel=%s, response_ts=%s",
        feedback_type,
        user_id,
        channel_id,
        response_ts,
    )

    return FeedbackRequest(
        feedback_type=feedback_type,
        user_id=user_id,
        channel_id=str(channel_id) if channel_id is not None else None,
        response_ts=str(response_ts) if response_ts is not None else None,
        team_id=str(team_id) if team_id is not None else None,
    )


def _log_feedback(request: FeedbackRequest, logger_: logging.Logger) -> None:
    """Structured logging of feedback data for metrics/analysis."""
    feedback_data = {
        "feedback_type": request.feedback_type,
        "user_id": request.user_id,
        "channel_id": request.channel_id,
        "response_ts": request.response_ts,
        "team_id": request.team_id,
    }

    logger_.info("feedback_event", extra={"feedback": feedback_data})


async def _send_acknowledgment(
    request: FeedbackRequest,
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Send ephemeral acknowledgment to the user, if possible."""
    if not request.channel_id or not request.response_ts:
        logger_.warning("Cannot send acknowledgment: missing channel_id or response_ts")
        return

    acknowledgment_text = "Thank you for your feedback! We use this to improve the assistant."

    try:
        client.chat_postEphemeral(
            channel=request.channel_id,
            user=request.user_id,
            text=acknowledgment_text,
            thread_ts=request.response_ts,
        )
        logger_.info("Sent feedback acknowledgment to user %s", request.user_id)
    except SlackApiError as e:
        # Log and continue — acknowledgements are best-effort
        logger_.warning("Failed to send feedback acknowledgment: %s", e)


async def assistant_feedback_handler(
    ack: Callable[..., object],
    body: Mapping[str, object],
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Handle assistant feedback action (thumbs up/down).

    This function:
    - Calls `ack` in a way that supports both sync and async ack implementations.
    - Validates the payload and logs feedback.
    - Attempts to send an ephemeral acknowledgment to the user.

    Args:
        ack: Acknowledge function provided by Bolt (may be sync or async)
        body: Action payload
        client: Slack WebClient for API calls
        logger_: Logger instance for this handler
    """
    # Call ack and await if necessary (keeps tests using AsyncMock happy)
    await safe_ack(ack)

    try:
        request = _extract_feedback_data(body, logger_)
    except InvalidRequestError:
        logger_.warning("Invalid feedback request")
        return

    _log_feedback(request, logger_)
    await _send_acknowledgment(request, client, logger_)
