from unittest.mock import AsyncMock

import pytest

from lsimons_bot.assistant.assistant_thread_started import assistant_thread_started


class TestAssistantThreadStarted:
    @pytest.mark.asyncio
    async def test_assistant_thread_started_happy_path(self) -> None:
        await assistant_thread_started(AsyncMock(), AsyncMock())
