from slack_bolt import App

from lsimons_bot.listeners import actions, commands, events, messages, shortcuts, views


def register_listeners(app: App) -> None:
    actions.register(app)
    commands.register(app)
    events.register(app)
    messages.register(app)
    shortcuts.register(app)
    views.register(app)
