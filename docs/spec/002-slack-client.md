# 002 - Slack Client Architecture

**Purpose:** Document the slack_bolt framework integration and event handler patterns used throughout the application

**Requirements:**
- Handle Slack events asynchronously (messages, mentions, home tab)
- Support AI Assistant API features (threading, status, suggested prompts)
- Maintain clean separation between event types and handlers
- Enable easy addition of new event handlers

**Design Approach:**
- Use `slack_bolt` AsyncApp for async event handling
- Use `AsyncAssistant` for AI Assistant API features
- Organize handlers by event type in separate modules (assistant, messages, home)
- Each module exposes a `register(app)` function to attach handlers
- One handler per file for clarity

**Implementation Notes:**

## Module Structure

Each feature module follows this pattern:

```python
# module/__init__.py
from slack_bolt.async_app import AsyncApp

def register(app: AsyncApp) -> None:
    # Register event handlers
    app.event("event_name")(handler_function)
```

## Handler Signatures

Slack Bolt uses dependency injection - handlers can request any combination of parameters:

```python
async def handler(
    # Event data
    event: dict[str, Any],           # The specific event payload
    body: dict[str, Any],             # Full request body
    payload: dict[str, Any],          # Same as event
    context: AsyncBoltContext,        # Request context

    # Actions
    say: AsyncSay,                    # Post message to channel
    ack: AsyncAck,                    # Acknowledge event
    respond: AsyncRespond,            # Respond to action

    # AI Assistant API (only available in assistant handlers)
    set_status: AsyncSetStatus,       # Update assistant status
    set_title: AsyncSetTitle,         # Set thread title
    set_suggested_prompts: AsyncSetSuggestedPrompts,  # Suggest next prompts

    # Clients
    client: AsyncWebClient,           # Slack API client
) -> None:
    pass
```

**Key points:**
- Only request parameters you need
- Type hints are required
- Parameters are automatically injected by slack_bolt
- See `slack_bolt.kwargs_injection.async_args.AsyncArgs` for full list

## Event Data Examples

### Assistant Message Event

```python
event = {
    "type": "message",
    "user": "U0A3M4171BK",
    "text": "hi",
    "channel": "D0A387NCE2W",
    "channel_type": "im",
    "thread_ts": "1765656590.063629",
    "ts": "1765657699.728009",
    "assistant_thread": {
        "action_token": "10113454590597.10138525474272.6d5f43aa145b052ce0f7650320d9767a"
    },
    "blocks": [...],
}

context = {
    "channel_id": "D0A387NCE2W",
    "thread_ts": "1765656590.063629",
    "user_id": "U0A3M4171BK",
    "bot_user_id": "U0A3BQUJQ5S",
    "enterprise_id": "E0A3BPH11QC",
}
```

### Message Event

```python
body = {
    "type": "event_callback",
    "event": {
        "type": "message",
        "text": "hello world",
        "user": "U123",
        "channel": "C123",
        "ts": "1234567890.123456",
        "bot_id": "B123",  # Present if from bot
    }
}
```

## Current Modules

### assistant/
Handles AI Assistant API events:
- `assistant_message`: User messages in assistant threads
- `assistant_thread_started`: New thread initialization

### messages/
Handles general message events:
- `message`: All message events (filters out bots)
- `app_mention`: @mentions of the bot

### home/
Handles app home tab:
- `app_home_opened`: User opens app home tab

## Adding New Handlers

1. Create handler file in appropriate module directory
2. Define async handler function with required parameters
3. Add registration in module's `__init__.py`
4. Create corresponding test file in tests/

Example:
```python
# lsimons_bot/messages/new_handler.py
async def new_handler(event: dict[str, Any], say: AsyncSay) -> None:
    await say("Response")

# lsimons_bot/messages/__init__.py
from .new_handler import new_handler

def register(app: AsyncApp) -> None:
    app.event("event_name")(new_handler)
```

## References

- [Slack Bolt Python](https://slack.dev/bolt-python/)
- [AsyncApp Documentation](https://slack.dev/bolt-python/api-docs/slack_bolt/async_app.html)
- [AI Assistant API](https://api.slack.com/docs/apps/ai)
