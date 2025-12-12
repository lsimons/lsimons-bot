"""Handler for assistant_thread_started event.

Triggered when a user opens a new AI assistant thread in a channel.
Sends welcome greeting and suggested prompts to guide user interaction.
"""

import logging
from typing import Any

from slack_bolt import Ack
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


async def assistant_thread_started_handler(
    ack: Ack,
    body: dict[str, Any],
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Handle assistant_thread_started event.

    Sends welcome greeting and suggested prompts when user opens an assistant thread.

    Args:
        ack: Acknowledge the event to Slack
        body: Event payload containing thread_id, channel_id, user_id
        client: Slack WebClient for API calls
        logger_: Logger instance for this handler
    """
    _ = ack()

    try:
        # Extract event data
        assistant_thread_id = body.get("assistant_thread_id")
        channel_id = body.get("channel_id")
        user_id = body.get("user_id")

        if not assistant_thread_id or not channel_id:
            logger_.warning(
                "Missing required fields in assistant_thread_started event: %s", body
            )
            return

        logger_.info(
            "Assistant thread started - thread: %s, channel: %s, user: %s",
            assistant_thread_id,
            channel_id,
            user_id,
        )

        # Get channel info for context
        try:
            channel_info = client.conversations_info(channel=channel_id)
            channel_name = channel_info.get("channel", {}).get("name", channel_id)
            channel_topic = (
                channel_info.get("channel", {}).get("topic", {}).get("value", "")
            )
        except SlackApiError as e:
            logger_.warning("Failed to get channel info for %s: %s", channel_id, str(e))
            channel_name = channel_id
            channel_topic = ""

        # Send welcome message (welcome greeting will be handled by Slack UI)
        try:
            _ = client.assistant.threads.set_status(  # pyright: ignore[reportAttributeAccessIssue]
                channel_id=channel_id,
                thread_id=assistant_thread_id,
                status="running",
            )
        except SlackApiError as e:
            logger_.warning("Failed to set thread status: %s", str(e))

        # Generate suggested prompts based on channel
        suggested_prompts = _generate_suggested_prompts(channel_name, channel_topic)

        # Set suggested prompts for the thread
        try:
            _ = client.assistant.threads.set_suggested_prompts(  # pyright: ignore[reportAttributeAccessIssue]
                channel_id=channel_id,
                thread_id=assistant_thread_id,
                prompts=suggested_prompts,
            )
            logger_.info(
                "Set %d suggested prompts for thread %s",
                len(suggested_prompts),
                assistant_thread_id,
            )
        except SlackApiError as e:
            logger_.warning("Failed to set suggested prompts: %s", str(e))

    except Exception as e:
        logger_.error(
            "Error in assistant_thread_started handler: %s", str(e), exc_info=True
        )


def _generate_suggested_prompts(
    channel_name: str, channel_topic: str | None = None
) -> list[dict[str, str]]:
    """Generate suggested prompts based on channel context.

    Creates a list of helpful prompt suggestions for users based on the channel
    they're in and what it's for.

    Args:
        channel_name: Name of the channel
        channel_topic: Optional description of the channel topic

    Returns:
        List of prompt dicts with title and description
    """
    # Default prompts that work for any channel
    prompts = [
        {
            "title": "Summarize",
            "description": "Summarize the recent discussion in this thread",
        },
        {
            "title": "Explain",
            "description": "Explain a concept or topic in simple terms",
        },
        {
            "title": "Help",
            "description": "Help me with a problem or question",
        },
    ]

    # Add channel-specific prompts if we have topic info
    if channel_topic:
        if any(
            keyword in channel_topic.lower()
            for keyword in ["engineering", "dev", "code", "tech"]
        ):
            prompts.insert(
                0,
                {
                    "title": "Code Review",
                    "description": "Review this code for issues or improvements",
                },
            )
        elif any(
            keyword in channel_topic.lower() for keyword in ["design", "ui", "ux"]
        ):
            prompts.insert(
                0,
                {
                    "title": "Design Feedback",
                    "description": "Give me feedback on this design",
                },
            )

    return prompts
