"""Backward-compatible imports for shortcuts listeners.

Deprecation: Import from lsimons_bot.listeners.shortcuts instead.
"""

import warnings

from lsimons_bot.listeners.shortcuts import register

warnings.warn(
    "Importing from 'listeners.shortcuts' is deprecated. "
    "Please use 'lsimons_bot.listeners.shortcuts' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["register"]
