import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from lsimons_bot.listeners import register_listeners

logging.basicConfig(level=logging.DEBUG)

# Initialization
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    ignoring_self_assistant_message_events_enabled=False,
)

# Register Listeners
register_listeners(app)


# Start Bolt app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
