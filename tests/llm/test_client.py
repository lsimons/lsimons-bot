from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lsimons_bot.llm.client import LLMClient


class TestLLMClient:
    @pytest.fixture
    def client(self) -> LLMClient:
        return LLMClient(base_url="http://localhost:8000", api_key="test-key", model="gpt-4")

    @pytest.mark.asyncio
    async def test_chat_completion(self, client: LLMClient) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"

        with patch.object(client.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
            result = await client.chat_completion([{"role": "user", "content": "Hello"}])
            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_chat_completion_empty_response(self, client: LLMClient) -> None:
        mock_response = MagicMock()
        mock_response.choices = []

        with patch.object(client.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
            result = await client.chat_completion([{"role": "user", "content": "Hello"}])
            assert result == ""

    @pytest.mark.asyncio
    async def test_chat_completion_stream(self, client: LLMClient) -> None:
        async def mock_stream():
            chunks = ["Hello", " ", "world"]
            for chunk_text in chunks:
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta.content = chunk_text
                yield chunk

        with patch.object(client.client.chat.completions, "create", new=AsyncMock(return_value=mock_stream())):
            result = []
            async for chunk in client.chat_completion_stream([{"role": "user", "content": "Hello"}]):
                result.append(chunk)
            assert result == ["Hello", " ", "world"]

    @pytest.mark.asyncio
    async def test_chat_completion_stream_empty_delta(self, client: LLMClient) -> None:
        async def mock_stream():
            chunk = MagicMock()
            chunk.choices = []
            yield chunk

        with patch.object(client.client.chat.completions, "create", new=AsyncMock(return_value=mock_stream())):
            result = []
            async for chunk in client.chat_completion_stream([{"role": "user", "content": "Hello"}]):
                result.append(chunk)
            assert result == []
