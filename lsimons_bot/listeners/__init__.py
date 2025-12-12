"""Registers all listeners with the Slack app."""

from slack_bolt import App

from . import actions, commands, events, messages, shortcuts, views


def register_listeners(app: App) -> None:
    """Register all listeners with the app."""
    actions.register(app)
    commands.register(app)
    events.register(app)
    messages.register(app)
    shortcuts.register(app)
    views.register(app)
