import logging
import random
from asyncio import sleep
from typing import Any, Dict, List

from slack_bolt.async_app import (
    AsyncBoltContext,
    AsyncSay,
    AsyncSetStatus,
    AsyncSetTitle,
)
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.web.async_slack_response import AsyncSlackResponse

logger = logging.getLogger(__name__)


loading_messages = [
    "Teaching the hamsters to type faster…",
    "Untangling the internet cables…",
    "Consulting the office goldfish…",
    "Polishing up the response just for you…",
    "Convincing the AI to stop overthinking…",
]

response_messages = [
    "That's interesting. Tell me more?",
    "What makes you say that?",
    "I'm not sure. Please elaborate.",
    "Can you provide more details?",
    "How does that make you feel?",
]


def pick_response_message() -> str:
    return random.choice(response_messages)


async def assistant_message(
    context: AsyncBoltContext,
    payload: Dict[str, Any],
    say: AsyncSay,
    set_status: AsyncSetStatus,
    set_title: AsyncSetTitle,
    client: AsyncWebClient,
) -> None:
    user_message = payload.get("text", "")
    logger.debug(">> assistant_message('%s',...)", user_message)
    channel_id = context.channel_id
    thread_ts = context.thread_ts
    messages: List[Dict[str, str]] = []

    await set_title(user_message)
    await set_status(status="thinking...", loading_messages=loading_messages)
    await sleep(0.05)

    if channel_id is not None and thread_ts is not None:
        try:
            messages = await read_thread(client, channel_id, thread_ts)
        except Exception as e:
            logger.error("Error reading the message thread: %s", e)
            await say(f"Error reading the message thread: {e}")
            return
    else:
        messages = [{"role": "user", "content": user_message}]
    logger.debug("message thread: %s", messages)

    await sleep(0.05)
    response = pick_response_message()
    await say(response)
    logger.debug("<< assistant_message()")


async def read_thread(
    client: AsyncWebClient, channel_id: str, thread_ts: str
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    replies: AsyncSlackResponse = await client.conversations_replies(
        channel=channel_id,
        ts=thread_ts,
        oldest=thread_ts,
        limit=100,
    )
    for message in replies.get("messages", []):
        message_text = message.get("text", "")
        if message_text.strip() == "":
            continue
        bot_id = message.get("bot_id")
        role = "user" if bot_id is None else "assistant"
        messages.append({"role": role, "content": message_text})
    return messages


# async app docs: https://docs.slack.dev/tools/bolt-python/reference/async_app.html

# async web client docs: https://docs.slack.dev/tools/python-slack-sdk/reference/web/async_client.html

# sample data from an invocation:
__event = {
    "assistant_thread": {
        "action_token": "10113454590597.10138525474272.6d5f43aa145b052ce0f7650320d9767a"
    },
    "blocks": [
        {
            "block_id": "a8bcU",
            "elements": [
                {
                    "elements": [{"text": "hi", "type": "text"}],
                    "type": "rich_text_section",
                }
            ],
            "type": "rich_text",
        }
    ],
    "channel": "D0A387NCE2W",
    "channel_type": "im",
    "client_msg_id": "ce133266-eb72-4cbe-9c25-5b8ee81fb66d",
    "event_ts": "1765657699.728009",
    "parent_user_id": "U0A3BQUJQ5S",
    "text": "hi",
    "thread_ts": "1765656590.063629",
    "ts": "1765657699.728009",
    "type": "message",
    "user": "U0A3M4171BK",
}
__context = {
    "ack": "<slack_bolt.context.ack.async_ack.AsyncAck object at 0x101bdcd70>",
    "actor_enterprise_id": "E0A3BPH11QC",
    "actor_user_id": "U0A3M4171BK",
    "authorize_result": {
        "bot_id": "B0A34Q56E5B",
        "bot_scopes": [
            "channels:history",
            "chat:write",
            "commands",
            "assistant:write",
            "im:history",
            "channels:read",
            "groups:read",
            "im:read",
            "mpim:read",
            "im:write",
            "app_mentions:read",
            "mpim:history",
        ],
        "bot_token": "xoxb-...",
        "bot_user_id": "U0A3BQUJQ5S",
        "enterprise_id": "E0A3BPH11QC",
        "team": None,
        "team_id": "E0A3BPH11QC",
        "url": None,
        "user": None,
        "user_id": "U0A3M4171BK",
        "user_scopes": None,
        "user_token": None,
    },
    "bot_id": "B0A34Q56E5B",
    "bot_token": "xoxb-...",
    "bot_user_id": "U0A3BQUJQ5S",
    "channel_id": "D0A387NCE2W",
    "client": "<slack_sdk.web.async_client.AsyncWebClient object at 0x101abafd0>",
    "complete": "<slack_bolt.context.complete.async_complete.AsyncComplete object at 0x101bdd010>",
    "enterprise_id": "E0A3BPH11QC",
    "fail": "<slack_bolt.context.fail.async_fail.AsyncFail object at 0x101bdd160>",
    "get_thread_context": "<slack_bolt.context.get_thread_context.async_get_thread_context.AsyncGetThreadContext object at 0x101bdcad0>",
    "is_enterprise_install": True,
    "listener_runner": "<slack_bolt.listener.asyncio_runner.AsyncioListenerRunner object at 0x101b49940>",
    "logger": "<Logger app.py (WARNING)>",
    "respond": "<slack_bolt.context.respond.async_respond.AsyncRespond object at 0x101bdcec0>",
    "save_thread_context": "<slack_bolt.context.save_thread_context.async_save_thread_context.AsyncSaveThreadContext object at 0x101bdcc20>",
    "say": "<slack_bolt.context.say.async_say.AsyncSay object at 0x101bdc050>",
    "set_status": "<slack_bolt.context.set_status.async_set_status.AsyncSetStatus object at 0x101bdc1a0>",
    "set_suggested_prompts": "<slack_bolt.context.set_suggested_prompts.async_set_suggested_prompts.AsyncSetSuggestedPrompts object at 0x101bdc980>",
    "set_title": "<slack_bolt.context.set_title.async_set_title.AsyncSetTitle object at 0x101bdc830>",
    "thread_ts": "1765656590.063629",
    "token": "xoxb-...",
    "user_id": "U0A3M4171BK",
}
__body = {
    "api_app_id": "A0A34Q4D20M",
    "authorizations": [
        {
            "enterprise_id": "E0A3BPH11QC",
            "is_bot": True,
            "is_enterprise_install": True,
            "team_id": None,
            "user_id": "U0A3BQUJQ5S",
        }
    ],
    "context_enterprise_id": "E0A3BPH11QC",
    "context_team_id": None,
    "enterprise_id": "E0A3BPH11QC",
    "event": {
        "assistant_thread": {"action_token": "10113454590597.10138525474272.6d...7a"},
        "blocks": [
            {
                "block_id": "a8bcU",
                "elements": [
                    {
                        "elements": [{"text": "hi", "type": "text"}],
                        "type": "rich_text_section",
                    }
                ],
                "type": "rich_text",
            }
        ],
        "channel": "D0A387NCE2W",
        "channel_type": "im",
        "client_msg_id": "ce133266-eb72-4cbe-9c25-5b8ee81fb66d",
        "event_ts": "1765657699.728009",
        "parent_user_id": "U0A3BQUJQ5S",
        "text": "hi",
        "thread_ts": "1765656590.063629",
        "ts": "1765657699.728009",
        "type": "message",
        "user": "U0A3M4171BK",
    },
    "event_context": "4-eyJld...cifQ",
    "event_id": "Ev0A495YPNKS",
    "event_time": 1765657699,
    "is_ext_shared_channel": False,
    "team_id": "T0A42FFDY80",
    "token": "mXV...8x",
    "type": "event_callback",
}
__payload = {
    "assistant_thread": {"action_token": "10113454590597.10138525474272.6d...7a"},
    "blocks": [
        {
            "block_id": "a8bcU",
            "elements": [
                {
                    "elements": [{"text": "hi", "type": "text"}],
                    "type": "rich_text_section",
                }
            ],
            "type": "rich_text",
        }
    ],
    "channel": "D0A387NCE2W",
    "channel_type": "im",
    "client_msg_id": "ce133266-eb72-4cbe-9c25-5b8ee81fb66d",
    "event_ts": "1765657699.728009",
    "parent_user_id": "U0A3BQUJQ5S",
    "text": "hi",
    "thread_ts": "1765656590.063629",
    "ts": "1765657699.728009",
    "type": "message",
    "user": "U0A3M4171BK",
}
