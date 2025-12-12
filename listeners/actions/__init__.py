"""Backward-compatible imports for actions listeners.

Deprecated: Import from lsimons_bot.listeners.actions instead.
"""

import warnings

from lsimons_bot.listeners.actions import register

warnings.warn(
    "Importing from 'listeners.actions' is deprecated. "
    "Please use 'lsimons_bot.listeners.actions' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["register"]
