from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from lsimons_bot.app.config import get_env_vars
from lsimons_bot.llm import LLMClient
from lsimons_bot.slack import assistant, home, messages


async def main() -> None:
    env_vars = get_env_vars()

    # Initialize LLM client (will be used by handlers)
    _ = LLMClient(
        base_url=env_vars["OPENAI_BASE_URL"],
        api_key=env_vars["OPENAI_API_KEY"],
        model=env_vars["OPENAI_MODEL"],
    )

    app = AsyncApp(
        token=env_vars["SLACK_BOT_TOKEN"],
        ignoring_self_assistant_message_events_enabled=False,
    )
    assistant.register(app)
    messages.register(app)
    home.register(app)

    handler = AsyncSocketModeHandler(app, env_vars["SLACK_APP_TOKEN"])
    await handler.start_async()
