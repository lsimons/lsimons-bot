"""Registers event listeners with the Slack app."""

from slack_bolt import App

from .assistant_thread_started import assistant_thread_started_handler
from .assistant_user_message import assistant_user_message_handler


def register(app: App) -> None:
    """Register event listeners."""
    app.event("assistant_thread_started")(assistant_thread_started_handler)
    app.event("assistant_user_message")(assistant_user_message_handler)
