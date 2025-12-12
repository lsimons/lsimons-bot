"""Backward-compatible imports from lsimons_bot.listeners.

This module provides backward compatibility for existing code that imports
from the old 'listeners' location. New code should import from
'lsimons_bot.listeners' instead.

Deprecation: The 'listeners' package at the root level will be removed in a
future version. Please update your imports to use 'lsimons_bot.listeners'.
"""

import warnings

from lsimons_bot.listeners import (
    actions,
    commands,
    events,
    messages,
    register_listeners,
    shortcuts,
    views,
)

warnings.warn(
    "Importing from 'listeners' is deprecated. "
    "Please use 'lsimons_bot.listeners' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "register_listeners",
    "actions",
    "commands",
    "events",
    "messages",
    "shortcuts",
    "views",
]
