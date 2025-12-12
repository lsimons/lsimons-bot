"""Fixtures and fakes for event listener tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from lsimons_bot.slack import ChannelInfo


class FakeSlackServices:
    """Fake Slack service objects for testing."""

    def __init__(self):
        self.get_channel_info = MagicMock()
        self.get_conversation_history = MagicMock(return_value=[])
        # Note: set_thread_status is not awaited in some code paths, so use MagicMock
        self.set_thread_status = MagicMock()
        self.set_suggested_prompts = MagicMock()

    def with_channel(
        self,
        channel_id: str = "C123",
        name: str = "general",
        topic: str = "",
        is_private: bool = False,
    ) -> "FakeSlackServices":
        """Configure fake channel info."""
        self.get_channel_info.return_value = ChannelInfo(
            id=channel_id,
            name=name,
            topic=topic,
            is_private=is_private,
        )
        return self

    def with_history(self, messages: list[dict[str, Any]]) -> "FakeSlackServices":
        """Configure fake conversation history."""
        self.get_conversation_history.return_value = messages
        return self


class FakeLLMServices:
    """Fake LLM service objects for testing."""

    def __init__(self):
        self.create_llm_client = MagicMock()
        self.client = AsyncMock()
        self.create_llm_client.return_value = self.client

    def with_streaming_response(self, chunks: list[str]) -> "FakeLLMServices":
        """Configure fake streaming response."""

        async def async_generator():
            for chunk in chunks:
                yield chunk

        self.client.stream_completion = MagicMock(return_value=async_generator())
        return self

    def with_error(self, error: Exception) -> "FakeLLMServices":
        """Configure fake to raise error."""
        self.client.stream_completion = MagicMock(side_effect=error)
        return self


@pytest.fixture
def fake_slack():
    """Provide fake Slack services."""
    return FakeSlackServices()


@pytest.fixture
def fake_llm():
    """Provide fake LLM services."""
    return FakeLLMServices()
