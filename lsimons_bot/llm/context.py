"""Context management for LLM interactions.

Provides utilities for retrieving conversation history, formatting context
for LLM prompts, and detecting assistant messages.
"""

import logging
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from lsimons_bot.slack.exceptions import SlackThreadError

logger = logging.getLogger(__name__)


def get_conversation_history(
    client: WebClient,
    channel: str,
    thread_ts: str,
) -> list[dict[str, str]]:
    """Retrieve conversation history from a thread and format as message list.

    Fetches all replies in a thread and formats them as a list of role/content
    dictionaries suitable for passing to LLM APIs.

    Args:
        client: Slack WebClient instance
        channel: Channel ID where thread exists
        thread_ts: Thread timestamp (parent message timestamp)

    Returns:
        List of message dicts with 'role' and 'content' keys.
        Format: [{"role": "user" | "assistant", "content": "..."}, ...]

    Raises:
        SlackThreadError: If thread retrieval fails
    """
    try:
        response = client.conversations_replies(
            channel=channel,
            ts=thread_ts,
        )
    except SlackApiError as e:
        logger.error(
            "Failed to retrieve thread history for %s:%s - %s",
            channel,
            thread_ts,
            str(e),
        )
        raise SlackThreadError(f"Failed to retrieve thread history: {str(e)}") from e

    messages: list[dict[str, str]] = []

    for msg in response.get("messages", []):
        # Skip message edits and other metadata
        if msg.get("subtype") in ("message_changed", "message_deleted"):
            continue

        role = "assistant" if is_assistant_message(msg) else "user"
        text = msg.get("text")

        # Skip messages with no text or empty text
        if not text:
            continue

        content = str(text)
        if content:
            messages.append({"role": role, "content": content})

    return messages


def format_thread_context(
    channel_name: str,
    channel_topic: str | None = None,
) -> str:
    """Format channel and thread context for inclusion in system prompts.

    Creates a human-readable string describing the channel context that can be
    prepended to LLM prompts.

    Args:
        channel_name: Name of the channel (e.g., "general", "engineering")
        channel_topic: Optional channel topic/description

    Returns:
        Formatted context string for system prompt inclusion
    """
    context = f"You are in channel #{channel_name}."

    if channel_topic:
        context += f" Channel topic: {channel_topic}"

    return context


def is_assistant_message(msg: dict[str, Any]) -> bool:
    """Detect if a message was sent by the bot assistant.

    Checks the message metadata to determine if it came from the bot user
    rather than a human user.

    Args:
        msg: Message object from Slack API

    Returns:
        True if message is from bot, False otherwise
    """
    # Check bot_profile presence (indicates message from bot)
    if msg.get("bot_profile"):
        return True

    # Check bot_id field
    if msg.get("bot_id"):
        return True

    # Check subtype for bot messages
    if msg.get("subtype") == "bot_message":
        return True

    return False
