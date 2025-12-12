"""Handler for assistant_user_message event.

Triggered when a user sends a message in an AI assistant thread.
Retrieves conversation history, calls LLM via LiteLLM proxy, and streams response.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Sequence, cast

from openai.types.chat import ChatCompletionMessageParam
from slack_sdk import WebClient

from lsimons_bot.listeners.utils import safe_ack
from lsimons_bot.llm import (
    LLMAPIError,
    LLMConfigurationError,
    build_system_prompt,
    create_llm_client,
    format_thread_context,
    get_conversation_history,
)
from lsimons_bot.slack import (
    ChannelInfo,
    InvalidRequestError,
    SlackChannelError,
    SlackThreadError,
    get_channel_info,
    set_thread_status,
)

logger = logging.getLogger(__name__)


@dataclass
class UserMessageRequest:
    """Validated user message request data."""

    thread_id: str
    channel_id: str
    user_message: str


async def assistant_user_message_handler(
    ack: Callable[..., object],
    body: dict[str, Any],
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Handle assistant_user_message event.

    Orchestrates: validation → context gathering → LLM call → response

    Args:
        ack: Acknowledge the event to Slack (may be sync or async)
        body: Event payload containing thread_id, channel_id, user_message, etc.
        client: Slack WebClient for API calls
        logger_: Logger instance for this handler
    """
    # Call ack and await if necessary to support both sync and async ack implementations
    await safe_ack(ack)

    try:
        request = _extract_request_data(body, logger_)
        await _process_user_message(request, client, logger_)
    except InvalidRequestError as e:
        logger_.warning("Invalid request: %s", e)
    except SlackChannelError as e:
        logger_.error("Channel error: %s", e)
        await _send_error_to_user(client, body, "Channel unavailable", logger_)
    except SlackThreadError as e:
        logger_.error("Thread error: %s", e)
        await _send_error_to_user(client, body, "Thread unavailable", logger_)
    except LLMConfigurationError as e:
        logger_.error("LLM configuration error: %s", e)
        await _send_error_to_user(client, body, "Configuration error. Please check settings.", logger_)
    except LLMAPIError as e:
        logger_.error("LLM API error: %s", e)
        await _send_error_to_user(client, body, "AI assistant unavailable", logger_)


def _extract_request_data(
    body: dict[str, Any],
    logger_: logging.Logger,
) -> UserMessageRequest:
    """Extract and validate request data from event body.

    Args:
        body: Event payload
        logger_: Logger instance

    Returns:
        Validated UserMessageRequest

    Raises:
        InvalidRequestError: If required fields are missing or invalid
    """
    thread_id_raw = body.get("assistant_thread_id", "")
    channel_id_raw = body.get("channel_id", "")
    user_message_raw = body.get("text", "")

    thread_id = str(thread_id_raw).strip() if thread_id_raw else ""
    channel_id = str(channel_id_raw).strip() if channel_id_raw else ""
    user_message = str(user_message_raw).strip() if user_message_raw else ""

    if not thread_id or not channel_id:
        raise InvalidRequestError("Missing required fields: assistant_thread_id or channel_id")

    if not user_message:
        raise InvalidRequestError("User message cannot be empty")

    logger_.info(
        "Processing user message in thread %s (channel: %s)",
        thread_id,
        channel_id,
    )

    return UserMessageRequest(
        thread_id=thread_id,
        channel_id=channel_id,
        user_message=user_message,
    )


async def _process_user_message(
    request: UserMessageRequest,
    client: WebClient,
    logger_: logging.Logger,
) -> None:
    """Process user message: gather context, call LLM, send response.

    Main workflow orchestrator. Delegates major steps to focused functions.

    Args:
        request: Validated user message request
        client: Slack WebClient
        logger_: Logger instance

    Raises:
        SlackChannelError, SlackThreadError, LLMAPIError, LLMConfigurationError
    """
    # Set thread to processing state
    set_thread_status(client, request.channel_id, request.thread_id, "running")

    # Gather context
    channel_info = get_channel_info(client, request.channel_id)
    history = get_conversation_history(client, request.channel_id, request.thread_id)

    # Generate response
    response_text = await _generate_llm_response(request, channel_info, history, logger_)

    if not response_text:
        logger_.warning("LLM returned empty response")
        raise LLMAPIError("Empty response from LLM")

    logger_.info("LLM response generated: %d characters", len(response_text))

    # Set thread back to waiting for user
    set_thread_status(
        client,
        request.channel_id,
        request.thread_id,
        "waiting_on_user",
    )


async def _generate_llm_response(
    request: UserMessageRequest,
    channel_info: ChannelInfo,
    history: Sequence[dict[str, str]],
    logger_: logging.Logger,
) -> str:
    """Generate LLM response using context.

    Builds system prompt with channel context, creates message list,
    calls LLM, and returns accumulated response.

    Args:
        request: User message request
        channel_info: Channel information object
        history: Conversation history from thread (sequence of role/content dicts)
        logger_: Logger instance

    Returns:
        Generated response text

    Raises:
        LLMAPIError: If LLM call fails
        LLMConfigurationError: If LLM is misconfigured
    """
    # Build messages for LLM (list of simple dicts)
    messages = _build_message_list(list(history), request.user_message)

    # Build system prompt with channel context
    channel_context = format_thread_context(
        channel_info.name,
        channel_info.topic if channel_info.topic else None,
    )
    system_prompt = build_system_prompt(context=channel_context)

    # Get model from environment
    model = os.getenv("ASSISTANT_MODEL", "azure/gpt-3.5-turbo")

    logger_.info(
        "Calling LLM with model %s, %d messages in history",
        model,
        len(messages),
    )

    # Call LLM and collect response
    response_text = ""
    llm_client = create_llm_client()
    try:
        # Cast each message to ChatCompletionMessageParam to satisfy the LLM client's type.
        messages_param: list[ChatCompletionMessageParam] = [
            cast(ChatCompletionMessageParam, cast(object, m)) for m in messages
        ]

        async for chunk in llm_client.stream_completion(
            model=model,
            messages=messages_param,
            system_prompt=system_prompt,
        ):
            response_text += chunk
    except (LLMAPIError, LLMConfigurationError):
        # Re-raise LLM exceptions (already wrapped with context)
        raise
    finally:
        await llm_client.close()

    return response_text


def _build_message_list(
    history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, str]]:
    """Build message list for LLM from history and new message.

    Args:
        history: Conversation history from Slack
        user_message: New user message

    Returns:
        List of message dicts with role and content
    """
    messages = list(history) if history else []
    messages.append({"role": "user", "content": user_message})
    return messages


async def _send_error_to_user(
    client: WebClient,
    body: dict[str, Any],
    error_message: str,
    logger_: logging.Logger,
) -> None:
    """Send user-friendly error message.

    Attempts to set thread status to waiting_on_user so user can retry.

    Args:
        client: Slack WebClient
        body: Original event body
        error_message: Error message to display
        logger_: Logger instance
    """
    thread_id_raw = body.get("assistant_thread_id")
    channel_id_raw = body.get("channel_id")

    thread_id = str(thread_id_raw) if thread_id_raw else ""
    channel_id = str(channel_id_raw) if channel_id_raw else ""

    if not thread_id or not channel_id:
        logger_.warning("Cannot send error: missing thread_id or channel_id")
        return

    try:
        set_thread_status(client, channel_id, thread_id, "waiting_on_user")
    except SlackThreadError as e:
        logger_.warning("Failed to set error status: %s", e)
