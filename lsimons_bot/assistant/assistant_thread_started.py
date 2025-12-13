import logging

from slack_bolt.async_app import (
    AsyncSay,
    AsyncSetSuggestedPrompts,
)

logger = logging.getLogger(__name__)


async def assistant_thread_started(say: AsyncSay, set_suggested_prompts: AsyncSetSuggestedPrompts) -> None:
    logger.debug(">> assistant_thread_started()")

    _ = await say(":wave: Hi, how can I help you today?")
    _ = await set_suggested_prompts(
        prompts=[
            "Who is Leo?",
            "Where is Leo?",
            "Why is Leo?",
        ]
    )

    logger.debug("<< assistant_thread_started()")
