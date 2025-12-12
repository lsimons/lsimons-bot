"""Handler for assistant_user_message event.

Triggered when a user sends a message in an AI assistant thread.
Retrieves conversation history, calls LLM via LiteLLM proxy, and streams response.
"""

import logging
import os
from typing import Any

from slack_bolt import Ack
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from listeners._assistant_utils import (
    format_thread_context,
    get_conversation_history,
)
from listeners._llm import create_llm_client

logger = logging.getLogger(__name__)


async def assistant_user_message_handler(
    ack: Ack,
    body: dict[str, Any],
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Handle assistant_user_message event.

    Retrieves thread context, calls LLM via LiteLLM proxy, and streams response
    to the user in the assistant thread.

    Args:
        ack: Acknowledge the event to Slack
        body: Event payload containing thread_id, channel_id, user_message, etc.
        client: Slack WebClient for API calls
        logger_: Logger instance for this handler
    """
    ack()

    try:
        # Extract event data
        assistant_thread_id = body.get("assistant_thread_id")
        channel_id = body.get("channel_id")
        user_message = body.get("text", "").strip()

        if not assistant_thread_id or not channel_id:
            logger_.warning("Missing required fields in assistant_user_message event: %s", body)
            return

        if not user_message:
            logger_.warning("Empty user message in thread %s", assistant_thread_id)
            return

        logger_.info(
            "Processing user message in thread %s (channel: %s)",
            assistant_thread_id,
            channel_id,
        )

        # Set thread status to indicate processing
        try:
            client.assistant.threads.set_status(
                channel_id=channel_id,
                thread_id=assistant_thread_id,
                status="running",
            )
        except SlackApiError as e:
            logger_.warning("Failed to set thread status: %s", str(e))

        # Get channel info for context
        channel_name = channel_id
        channel_topic = ""
        try:
            channel_info = client.conversations_info(channel=channel_id)
            channel_name = channel_info.get("channel", {}).get("name", channel_id)
            channel_topic = channel_info.get("channel", {}).get("topic", {}).get("value", "")
        except SlackApiError as e:
            logger_.warning("Failed to get channel info for %s: %s", channel_id, str(e))

        # Get conversation history from thread
        try:
            conversation_history = get_conversation_history(client, channel_id, assistant_thread_id)
        except SlackApiError as e:
            logger_.error("Failed to get conversation history: %s", str(e))
            conversation_history = []

        # Build messages for LLM
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": user_message})

        # Get system prompt and model from environment
        system_prompt = (
            os.getenv("ASSISTANT_SYSTEM_PROMPT", "You are a helpful assistant.")
            + "\n\n"
            + format_thread_context(channel_name, channel_topic if channel_topic else None)
        )

        model = os.getenv("ASSISTANT_MODEL", "azure/gpt-5-mini")

        logger_.info(
            "Calling LLM with model %s, %d messages in history",
            model,
            len(messages),
        )

        # Call LLM and stream response
        response_text = ""
        try:
            llm_client = create_llm_client()
            async for chunk in llm_client.stream_completion(
                model=model,
                messages=messages,
                system_prompt=system_prompt,
            ):
                response_text += chunk

            await llm_client.close()
        except ValueError as e:
            logger_.error("LLM configuration error: %s", str(e))
            _send_error_message(
                client,
                channel_id,
                assistant_thread_id,
                "Configuration error. Please check LiteLLM settings.",
                logger_,
            )
            return
        except Exception as e:
            logger_.error("LLM request failed: %s", str(e), exc_info=True)
            _send_error_message(
                client,
                channel_id,
                assistant_thread_id,
                "I encountered an error processing your message. Please try again.",
                logger_,
            )
            return

        if not response_text:
            logger_.warning("LLM returned empty response")
            _send_error_message(
                client,
                channel_id,
                assistant_thread_id,
                "I couldn't generate a response. Please try again.",
                logger_,
            )
            return

        logger_.info("LLM response generated: %d characters", len(response_text))

        # Post the response to the thread
        try:
            client.assistant.threads.set_status(
                channel_id=channel_id,
                thread_id=assistant_thread_id,
                status="waiting_on_user",
            )
        except SlackApiError as e:
            logger_.warning("Failed to set final thread status: %s", str(e))

    except Exception as e:
        logger_.error("Error in assistant_user_message handler: %s", str(e), exc_info=True)


def _send_error_message(
    client: WebClient,
    channel_id: str,
    thread_id: str,
    error_message: str,
    logger_: logging.Logger,
) -> None:
    """Send an error message to the user in the assistant thread.

    Args:
        client: Slack WebClient for API calls
        channel_id: Channel ID where thread exists
        thread_id: Thread ID (assistant thread timestamp)
        error_message: Error message to send to user
        logger_: Logger instance
    """
    try:
        client.assistant.threads.set_status(
            channel_id=channel_id,
            thread_id=thread_id,
            status="waiting_on_user",
        )
    except SlackApiError as e:
        logger_.warning("Failed to set error status: %s", str(e))
