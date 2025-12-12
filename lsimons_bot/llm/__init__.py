"""LLM module for AI assistant functionality.

Provides interfaces and implementations for LLM interactions through LiteLLM,
including prompt engineering, conversation context management, and error handling.
"""

from lsimons_bot.llm.client import LiteLLMClient, create_llm_client
from lsimons_bot.llm.context import (
    format_thread_context,
    get_conversation_history,
    is_assistant_message,
)
from lsimons_bot.llm.exceptions import (
    LLMAPIError,
    LLMConfigurationError,
    LLMError,
    LLMQuotaExceededError,
    LLMTimeoutError,
)
from lsimons_bot.llm.prompt import (
    build_message_context,
    build_system_prompt,
    estimate_tokens,
    format_for_slack,
    get_suggested_prompts,
    trim_messages_for_context,
)

__all__ = [
    # Client
    "LiteLLMClient",
    "create_llm_client",
    # Exceptions
    "LLMError",
    "LLMConfigurationError",
    "LLMAPIError",
    "LLMTimeoutError",
    "LLMQuotaExceededError",
    # Prompts
    "build_system_prompt",
    "get_suggested_prompts",
    "format_for_slack",
    "trim_messages_for_context",
    "estimate_tokens",
    "build_message_context",
    # Context
    "get_conversation_history",
    "format_thread_context",
    "is_assistant_message",
]
