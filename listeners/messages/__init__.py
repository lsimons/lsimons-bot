"""Backward-compatible imports for messages listener.

This module provides backward compatibility for existing code.
New code should import from 'lsimons_bot.listeners.messages' instead.
"""

import warnings

from lsimons_bot.listeners.messages import register

warnings.warn(
    "Importing from 'listeners.messages' is deprecated. "
    "Please use 'lsimons_bot.listeners.messages' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["register"]
