import pytest

from lsimons_bot.messages.message import message


class TestMessage:
    @pytest.mark.asyncio
    async def test_message_happy_path(self) -> None:
        await message({"event": {"text": "hello"}})

    @pytest.mark.asyncio
    async def test_message_ignores_bot_messages(self) -> None:
        await message({"event": {"text": "hello", "bot_id": "B123"}})
