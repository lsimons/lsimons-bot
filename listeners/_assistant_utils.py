"""Backward-compatible imports for assistant utilities module.

This module provides backward compatibility for existing code that imports
from 'listeners._assistant_utils'. New code should import from 'lsimons_bot.llm' instead.

Deprecation: Direct imports from 'listeners._assistant_utils' will be removed in a
future version. Please update your imports to use 'lsimons_bot.llm'.
"""

import warnings

from lsimons_bot.llm.context import (
    format_thread_context,
    get_conversation_history,
    is_assistant_message,
)

warnings.warn(
    "Importing from 'listeners._assistant_utils' is deprecated. "
    "Please use 'lsimons_bot.llm' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "get_conversation_history",
    "format_thread_context",
    "is_assistant_message",
]
