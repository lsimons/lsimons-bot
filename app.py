import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from lsimons_bot.config import get_socket_mode_env_vars
from lsimons_bot.listeners import register_listeners

logging.basicConfig(level=logging.DEBUG)

# Validate environment variables
env_vars = get_socket_mode_env_vars()

# Initialization
app = App(
    token=env_vars["SLACK_BOT_TOKEN"],
    ignoring_self_assistant_message_events_enabled=False,
)

# Register Listeners
register_listeners(app)


# Start Bolt app
if __name__ == "__main__":
    SocketModeHandler(app, env_vars["SLACK_APP_TOKEN"]).start()
