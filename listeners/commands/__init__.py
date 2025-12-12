"""Backward-compatible imports for commands listener module.

This module provides backward compatibility for existing code.
New code should import from 'lsimons_bot.listeners.commands' instead.
"""

import warnings

from lsimons_bot.listeners.commands import register

warnings.warn(
    "Importing from 'listeners.commands' is deprecated. "
    "Please use 'lsimons_bot.listeners.commands' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["register"]
