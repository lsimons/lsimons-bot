"""Slack-related exceptions for the lsimons_bot package."""


class SlackError(Exception):
    """Base exception for all Slack-related errors."""

    pass


class SlackChannelError(SlackError):
    """Exception raised for channel-related operations."""

    pass


class SlackThreadError(SlackError):
    """Exception raised for thread-related operations."""

    pass


class SlackAPIError(SlackError):
    """Exception raised for Slack API errors."""

    pass


class SlackAuthError(SlackError):
    """Exception raised for authentication/authorization errors."""

    pass


class InvalidRequestError(SlackError):
    """Exception raised for invalid requests."""

    pass
