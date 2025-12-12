"""Registers action listeners with the Slack app."""

from slack_bolt import App

from .assistant_feedback import assistant_feedback_handler


def register(app: App) -> None:
    """Register action listeners."""
    app.action("feedback_thumbs_up")(assistant_feedback_handler)
    app.action("feedback_thumbs_down")(assistant_feedback_handler)
