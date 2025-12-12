"""Handler for assistant feedback actions.

Triggered when users click thumbs up/down buttons on assistant responses.
Logs feedback and sends acknowledgment to user.
"""

import logging
from dataclasses import dataclass
from typing import Any

from slack_bolt import Ack
from slack_sdk import WebClient

from lsimons_bot.slack import InvalidRequestError

logger = logging.getLogger(__name__)


@dataclass
class FeedbackRequest:
    """Validated feedback action data."""

    feedback_type: str  # "positive" or "negative"
    user_id: str
    channel_id: str | None
    response_ts: str | None
    team_id: str | None


async def assistant_feedback_handler(
    ack: Ack,
    body: dict[str, Any],
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Handle assistant feedback action (thumbs up/down).

    Orchestrates: validation → logging → acknowledgment

    Args:
        ack: Acknowledge the action to Slack
        body: Action payload containing feedback_type and message metadata
        client: Slack WebClient for API calls
        logger_: Logger instance for this handler
    """
    await ack()

    try:
        request = _extract_feedback_data(body, logger_)
        _log_feedback(request, logger_)
        await _send_acknowledgment(request, client, logger_)
    except InvalidRequestError as e:
        logger_.warning("Invalid feedback request: %s", e)
    except Exception as e:
        logger_.error(
            "Unexpected error in assistant_feedback_handler: %s",
            str(e),
            exc_info=True,
        )


def _extract_feedback_data(
    body: dict[str, Any],
    logger_: logging.Logger,
) -> FeedbackRequest:
    """Extract and validate feedback action data.

    Args:
        body: Action payload
        logger_: Logger instance

    Returns:
        Validated FeedbackRequest

    Raises:
        InvalidRequestError: If required fields are missing
    """
    actions = body.get("actions", [])
    if not actions:
        raise InvalidRequestError("No actions in feedback payload")

    action_value = actions[0].get("value", "").strip()
    user_id = body.get("user", {}).get("id", "").strip()
    channel_id = body.get("channel", {}).get("id")
    response_ts = body.get("message", {}).get("ts")
    team_id = body.get("team", {}).get("id")

    if not action_value or not user_id:
        raise InvalidRequestError("Missing required fields: action_value or user_id")

    # Map action value to feedback type
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
        channel_id=channel_id,
        response_ts=response_ts,
        team_id=team_id,
    )


def _log_feedback(
    request: FeedbackRequest,
    logger_: logging.Logger,
) -> None:
    """Log feedback metrics for analysis.

    Structured logging of feedback data for future analysis of assistant
    performance and user satisfaction.

    Args:
        request: Validated feedback request
        logger_: Logger instance
    """
    feedback_data = {
        "feedback_type": request.feedback_type,
        "user_id": request.user_id,
        "channel_id": request.channel_id,
        "response_ts": request.response_ts,
        "team_id": request.team_id,
    }

    # Log at info level with structured data (could be sent to metrics service)
    logger_.info(
        "feedback_event",
        extra={
            "feedback": feedback_data,
        },
    )


async def _send_acknowledgment(
    request: FeedbackRequest,
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Send acknowledgment message to user.

    Args:
        request: Feedback request with channel and thread info
        client: Slack WebClient
        logger_: Logger instance
    """
    if not request.channel_id or not request.response_ts:
        logger_.warning("Cannot send acknowledgment: missing channel_id or response_ts")
        return

    acknowledgment_text = (
        "Thank you for your feedback! We use this to improve the assistant."
    )

    try:
        client.chat_postEphemeral(
            channel=request.channel_id,
            user=request.user_id,
            text=acknowledgment_text,
            thread_ts=request.response_ts,
        )
        logger_.info("Sent feedback acknowledgment to user %s", request.user_id)
    except Exception as e:
        logger_.warning("Failed to send feedback acknowledgment: %s", e)
