"""Handler for assistant_thread_started event.

Triggered when a user opens a new AI assistant thread in a channel.
Sends welcome greeting and suggested prompts to guide user interaction.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable

from slack_sdk import WebClient

from lsimons_bot.listeners.utils import safe_ack
from lsimons_bot.llm import get_suggested_prompts
from lsimons_bot.slack import (
    InvalidRequestError,
    SlackChannelError,
    get_channel_info,
    set_suggested_prompts,
    set_thread_status,
)

logger = logging.getLogger(__name__)


@dataclass
class ThreadStartedRequest:
    """Validated thread started request data."""

    thread_id: str
    channel_id: str
    user_id: str


async def assistant_thread_started_handler(
    ack: Callable[..., object],
    body: dict[str, Any],
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Handle assistant_thread_started event.

    Orchestrates: validation → initialization → context gathering → setup

    Args:
        ack: Acknowledge the event to Slack
        body: Event payload containing thread_id, channel_id, user_id
        client: Slack WebClient for API calls
        logger_: Logger instance for this handler
    """
    # ack may be sync or async; call and await if necessary
    await safe_ack(ack)

    try:
        request = _extract_thread_data(body, logger_)
        await _initialize_thread(request, client, logger_)
    except InvalidRequestError as e:
        logger_.warning("Invalid request: %s", e)
    except SlackChannelError as e:
        logger_.error("Channel error: %s", e)


def _extract_thread_data(
    body: dict[str, Any],
    logger_: logging.Logger,
) -> ThreadStartedRequest:
    """Extract and validate thread started event data.

    Args:
        body: Event payload
        logger_: Logger instance

    Returns:
        Validated ThreadStartedRequest

    Raises:
        InvalidRequestError: If required fields are missing
    """
    thread_id = body.get("assistant_thread_id", "").strip()
    channel_id = body.get("channel_id", "").strip()
    user_id = body.get("user_id", "").strip()

    if not thread_id or not channel_id:
        raise InvalidRequestError("Missing required fields: assistant_thread_id or channel_id")

    logger_.info(
        "Assistant thread started - thread: %s, channel: %s, user: %s",
        thread_id,
        channel_id,
        user_id,
    )

    return ThreadStartedRequest(
        thread_id=thread_id,
        channel_id=channel_id,
        user_id=user_id,
    )


async def _initialize_thread(
    request: ThreadStartedRequest,
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Initialize assistant thread with status and suggested prompts.

    Sets thread to running status and provides channel-specific suggestions.

    Args:
        request: Validated thread started request
        client: Slack WebClient
        logger_: Logger instance

    Raises:
        SlackChannelError: If Slack operations fail
    """
    # Get channel info for context
    channel_info = get_channel_info(client, request.channel_id)

    # Set thread to running status
    set_thread_status(client, request.channel_id, request.thread_id, "running")

    # Generate and set suggested prompts based on channel topic
    suggested_prompts = get_suggested_prompts(channel_info.topic)

    set_suggested_prompts(
        client,
        request.channel_id,
        request.thread_id,
        suggested_prompts,
    )

    logger_.info(
        "Initialized thread %s with %d suggested prompts",
        request.thread_id,
        len(suggested_prompts),
    )
