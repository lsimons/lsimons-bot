"""Handler for assistant feedback actions.

Triggered when users click thumbs up/down buttons on assistant responses.
Logs feedback and sends acknowledgment to user.
"""

import logging
from typing import Any

from slack_bolt import Ack
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


async def assistant_feedback_handler(
    ack: Ack,
    body: dict[str, Any],
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Handle assistant feedback action (thumbs up/down).

    Logs user feedback on assistant responses and sends acknowledgment.

    Args:
        ack: Acknowledge the action to Slack
        body: Action payload containing feedback_type and message metadata
        client: Slack WebClient for API calls
        logger_: Logger instance for this handler
    """
    _ = ack()

    try:
        # Extract action data
        action_value = body.get("actions", [{}])[0].get("value", "")
        user_id = body.get("user", {}).get("id")
        channel_id = body.get("channel", {}).get("id")
        response_ts = body.get("message", {}).get("ts")
        team_id = body.get("team", {}).get("id")

        if not action_value or not user_id:
            logger_.warning("Missing required fields in feedback action: %s", body)
            return

        # Map action value to feedback type
        feedback_type = (
            "positive" if action_value == "feedback_thumbs_up" else "negative"
        )

        logger_.info(
            "Received feedback: type=%s, user=%s, channel=%s, response_ts=%s",
            feedback_type,
            user_id,
            channel_id,
            response_ts,
        )

        # Log feedback with metadata for analysis
        _log_feedback_metrics(
            feedback_type=feedback_type,
            user_id=user_id,
            channel_id=channel_id,
            response_ts=response_ts,
            team_id=team_id,
            logger_=logger_,
        )

        # Send acknowledgment to user
        acknowledgment_text = (
            "Thank you for your feedback! We use this to improve the assistant."
        )

        try:
            _ = client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=acknowledgment_text,
                thread_ts=response_ts,
            )
            logger_.info("Sent feedback acknowledgment to user %s", user_id)
        except SlackApiError as e:
            logger_.warning("Failed to send feedback acknowledgment: %s", str(e))

    except Exception as e:
        logger_.error("Error in assistant_feedback_handler: %s", str(e), exc_info=True)


def _log_feedback_metrics(
    feedback_type: str,
    user_id: str | None,
    channel_id: str | None,
    response_ts: str | None,
    team_id: str | None,
    logger_: logging.Logger,
) -> None:
    """Log feedback metrics for analysis and monitoring.

    Structured logging of feedback data for future analysis of assistant
    performance and user satisfaction.

    Args:
        feedback_type: "positive" or "negative"
        user_id: ID of user providing feedback
        channel_id: Channel where feedback occurred
        response_ts: Timestamp of the assistant response being reviewed
        team_id: Workspace ID
        logger_: Logger instance
    """
    # Structure feedback data for metrics/analytics
    feedback_data = {
        "feedback_type": feedback_type,
        "user_id": user_id,
        "channel_id": channel_id,
        "response_ts": response_ts,
        "team_id": team_id,
    }

    # Log at info level with structured data (could be sent to metrics service)
    logger_.info(
        "feedback_event",
        extra={
            "feedback": feedback_data,
        },
    )
