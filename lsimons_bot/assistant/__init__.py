from slack_bolt.async_app import AsyncApp, AsyncAssistant

from .assistant_message import assistant_message
from .assistant_thread_started import assistant_thread_started


def register(app: AsyncApp) -> None:
    assistant = AsyncAssistant()
    _ = assistant.thread_started(assistant_thread_started)
    _ = assistant.user_message(assistant_message)
    _ = app.use(assistant)
