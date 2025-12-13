from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lsimons_bot.assistant.assistant_message import assistant_message, read_thread


class TestReadThread:
    @pytest.mark.asyncio
    async def test_read_thread_happy_path(self) -> None:
        mock_client = MagicMock()
        mock_response = {
            "messages": [
                {"text": "user message"},
                {"text": "  "},
                {"text": "bot response", "bot_id": "B123"},
            ]
        }
        mock_client.conversations_replies = AsyncMock(return_value=mock_response)

        messages = await read_thread(mock_client, "C123", "1234567890.123456")

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


class TestAssistantMessage:
    async def _call_assistant_message(self, channel_id: str | None, thread_ts: str | None, mock_client: MagicMock) -> None:
        mock_context = MagicMock()
        mock_context.channel_id = channel_id
        mock_context.thread_ts = thread_ts

        with patch("lsimons_bot.assistant.assistant_message.sleep", new=AsyncMock()):
            await assistant_message(
                mock_context,
                {"text": "hello"},
                AsyncMock(),
                AsyncMock(),
                AsyncMock(),
                mock_client,
            )

    @pytest.mark.asyncio
    async def test_assistant_message_happy_path(self) -> None:
        await self._call_assistant_message(None, None, MagicMock())

    @pytest.mark.asyncio
    async def test_assistant_message_with_thread(self) -> None:
        mock_client = MagicMock()
        mock_client.conversations_replies = AsyncMock(return_value={"messages": [{"text": "hello"}]})

        await self._call_assistant_message("C123", "1234567890.123456", mock_client)

    @pytest.mark.asyncio
    async def test_assistant_message_error_handling(self) -> None:
        mock_client = MagicMock()
        mock_client.conversations_replies = AsyncMock(side_effect=Exception("API error"))

        await self._call_assistant_message("C123", "1234567890.123456", mock_client)
