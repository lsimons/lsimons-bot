"""Slack integration module for lsimons_bot.

This module provides utilities and abstractions for interacting with Slack,
including channel operations, thread management, and error handling.
"""

from lsimons_bot.slack.exceptions import (
    InvalidRequestError,
    SlackChannelError,
    SlackError,
    SlackThreadError,
)

__all__ = [
    "SlackError",
    "SlackChannelError",
    "SlackThreadError",
    "InvalidRequestError",
]
