"""Backward-compatible imports for LLM module.

This module provides backward compatibility for existing code that imports
from 'listeners._llm'. New code should import from 'lsimons_bot.llm' instead.

Deprecation: Direct imports from 'listeners._llm' will be removed in a future
version. Please update your imports to use 'lsimons_bot.llm'.
"""

import warnings

from lsimons_bot.llm.client import LiteLLMClient, create_llm_client

warnings.warn(
    "Importing from 'listeners._llm' is deprecated. " "Please use 'lsimons_bot.llm' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "LiteLLMClient",
    "create_llm_client",
]
