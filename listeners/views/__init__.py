"""Backward-compatible imports for views listener module.

Deprecated: Use lsimons_bot.listeners.views instead.
"""

import warnings

from lsimons_bot.listeners.views import register

warnings.warn(
    "Importing from 'listeners.views' is deprecated. "
    "Please use 'lsimons_bot.listeners.views' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["register"]
