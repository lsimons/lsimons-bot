import logging

from slack_bolt import App, BoltResponse
from slack_bolt.oauth.callback_options import CallbackOptions, FailureArgs, SuccessArgs
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from lsimons_bot.config import get_oauth_env_vars
from lsimons_bot.listeners import register_listeners

logging.basicConfig(level=logging.DEBUG)

# Validate environment variables
env_vars = get_oauth_env_vars()


# Callback to run on successful installation
def success(args: SuccessArgs) -> BoltResponse:
    # Call default handler to return an HTTP response
    return args.default.success(args)
    # return BoltResponse(status=200, body="Installation successful!")


# Callback to run on failed installation
def failure(args: FailureArgs) -> BoltResponse:
    return args.default.failure(args)
    # return BoltResponse(status=args.suggested_status_code, body=args.reason)


# Initialization
app = App(
    signing_secret=env_vars["SLACK_SIGNING_SECRET"],
    installation_store=FileInstallationStore(),
    oauth_settings=OAuthSettings(
        client_id=env_vars["SLACK_CLIENT_ID"],
        client_secret=env_vars["SLACK_CLIENT_SECRET"],
        scopes=["channels:history", "chat:write", "commands"],
        user_scopes=[],
        redirect_uri=None,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        state_store=FileOAuthStateStore(expiration_seconds=600),
        callback_options=CallbackOptions(success=success, failure=failure),
    ),
)

# Register Listeners
register_listeners(app)

# Start Bolt app
if __name__ == "__main__":
    app.start(3000)
