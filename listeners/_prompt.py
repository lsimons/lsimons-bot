"""Backward-compatible imports for prompt module.

This module provides backward compatibility for existing code that imports
from 'listeners._prompt'. New code should import from 'lsimons_bot.llm' instead.

Deprecation: Direct imports from 'listeners._prompt' will be removed in a future
version. Please update your imports to use 'lsimons_bot.llm'.
"""

import warnings

from lsimons_bot.llm.prompt import (
    build_message_context,
    build_system_prompt,
    estimate_tokens,
    format_for_slack,
    get_suggested_prompts,
    trim_messages_for_context,
)

warnings.warn(
    "Importing from 'listeners._prompt' is deprecated. " "Please use 'lsimons_bot.llm' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "build_system_prompt",
    "get_suggested_prompts",
    "format_for_slack",
    "trim_messages_for_context",
    "estimate_tokens",
    "build_message_context",
]
