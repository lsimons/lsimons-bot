"""Backward-compatible imports for events listeners.

This module re-exports from lsimons_bot.listeners.events for backward compatibility.
New code should import from lsimons_bot.listeners.events instead.
"""

import warnings

from lsimons_bot.listeners.events import register

warnings.warn(
    "Importing from 'listeners.events' is deprecated. "
    "Please use 'lsimons_bot.listeners.events' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["register"]
