"""Unit tests for LiteLLM integration module.

Tests cover:
- Client initialization with various configurations
- Streaming completions with proper chunk handling
- Non-streaming completions
- Error handling (API errors, connection errors, rate limiting, authentication)
- System prompt injection
- Async context manager
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError

from lsimons_bot.llm.client import LiteLLMClient, create_llm_client
from lsimons_bot.llm.exceptions import (
    LLMAPIError,
    LLMConfigurationError,
    LLMQuotaExceededError,
    LLMTimeoutError,
)


class TestLiteLLMClientInit:
    """Tests for LiteLLMClient initialization."""

    def test_init_with_explicit_api_key(self):
        """Client initializes with explicit api_key parameter."""
        client = LiteLLMClient(
            api_key="test-key",
            base_url="https://test.example.com/",
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://test.example.com/"
        assert client.timeout == 60.0

    def test_init_with_env_vars(self, monkeypatch):
        """Client initializes from environment variables."""
        monkeypatch.setenv("LITELLM_API_KEY", "env-key")
        monkeypatch.setenv("LITELLM_API_BASE", "https://env.example.com/")

        client = LiteLLMClient()
        assert client.api_key == "env-key"
        assert client.base_url == "https://env.example.com/"

    def test_init_missing_api_key_raises_error(self, monkeypatch):
        """Client raises LLMConfigurationError if api_key not provided."""
        monkeypatch.delenv("LITELLM_API_KEY", raising=False)

        with pytest.raises(LLMConfigurationError, match="LITELLM_API_KEY"):
            LiteLLMClient()

    def test_init_custom_timeout(self):
        """Client accepts custom timeout parameter."""
        client = LiteLLMClient(
            api_key="test-key",
            timeout=120.0,
        )
        assert client.timeout == 120.0

    def test_init_with_custom_base_url_from_env(self, monkeypatch):
        """Client prefers explicit base_url over environment variable."""
        monkeypatch.setenv("LITELLM_API_BASE", "https://env.example.com/")
        client = LiteLLMClient(
            api_key="test-key",
            base_url="https://explicit.example.com/",
        )
        assert client.base_url == "https://explicit.example.com/"

    def test_init_default_base_url(self, monkeypatch):
        """Client uses default LiteLLM proxy URL if not provided."""
        monkeypatch.delenv("LITELLM_API_BASE", raising=False)

        client = LiteLLMClient(api_key="test-key")
        assert client.base_url == "https://litellm.sbp.ai/"


class TestStreamCompletion:
    """Tests for streaming completion functionality."""

    @pytest.mark.asyncio
    async def test_stream_completion_basic(self):
        """Stream completion yields text chunks from response."""
        client = LiteLLMClient(api_key="test-key")

        # Mock streaming response
        mock_chunk_1 = MagicMock()
        mock_chunk_1.choices = [MagicMock(delta=MagicMock(content="Hello "))]
        mock_chunk_2 = MagicMock()
        mock_chunk_2.choices = [MagicMock(delta=MagicMock(content="world"))]
        mock_chunk_3 = MagicMock()
        mock_chunk_3.choices = [MagicMock(delta=MagicMock(content=None))]

        async def mock_stream_gen():
            for chunk in [mock_chunk_1, mock_chunk_2, mock_chunk_3]:
                yield chunk

        mock_response = mock_stream_gen()

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            chunks = []
            async for chunk in client.stream_completion(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
            ):
                chunks.append(chunk)

        assert chunks == ["Hello ", "world"]

    @pytest.mark.asyncio
    async def test_stream_completion_with_system_prompt(self):
        """Stream completion prepends system prompt to messages."""
        client = LiteLLMClient(api_key="test-key")

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]

        async def mock_stream_gen():
            yield mock_chunk

        mock_response = mock_stream_gen()

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            async for _ in client.stream_completion(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful",
            ):
                pass

        # Verify system prompt was prepended
        call_kwargs = mock_create.call_args[1]
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0] == {
            "role": "system",
            "content": "You are helpful",
        }

    @pytest.mark.asyncio
    async def test_stream_completion_passes_temperature_and_tokens(self):
        """Stream completion passes temperature and max_tokens to API."""
        client = LiteLLMClient(api_key="test-key")

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="test"))]

        async def mock_stream_gen():
            yield mock_chunk

        mock_response = mock_stream_gen()

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            async for _ in client.stream_completion(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
                temperature=0.5,
                max_tokens=100,
            ):
                pass

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_stream_completion_with_none_content(self):
        """Stream completion skips chunks with None content."""
        client = LiteLLMClient(api_key="test-key")

        mock_chunk_1 = MagicMock()
        mock_chunk_1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
        mock_chunk_2 = MagicMock()
        mock_chunk_2.choices = [MagicMock(delta=MagicMock(content=None))]
        mock_chunk_3 = MagicMock()
        mock_chunk_3.choices = [MagicMock(delta=MagicMock(content="world"))]

        async def mock_stream_gen():
            yield mock_chunk_1
            yield mock_chunk_2
            yield mock_chunk_3

        mock_response = mock_stream_gen()

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            chunks = []
            async for chunk in client.stream_completion(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
            ):
                chunks.append(chunk)

        assert chunks == ["Hello", "world"]

    @pytest.mark.asyncio
    async def test_stream_completion_timeout_error(self):
        """Stream completion raises LLMTimeoutError on timeout."""
        client = LiteLLMClient(api_key="test-key")

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Request timed out"),
        ):
            with pytest.raises(LLMTimeoutError):
                async for _ in client.stream_completion(
                    model="openai/gpt-4",
                    messages=[{"role": "user", "content": "Hi"}],
                ):
                    pass

    @pytest.mark.asyncio
    async def test_stream_completion_quota_error(self):
        """Stream completion raises LLMQuotaExceededError on quota issues."""
        client = LiteLLMClient(api_key="test-key")

        async def raise_rate_limit(*args, **kwargs):
            raise RateLimitError("Rate limit exceeded", response=MagicMock(), body=None)

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=raise_rate_limit,
        ):
            with pytest.raises(LLMQuotaExceededError):
                async for _ in client.stream_completion(
                    model="openai/gpt-4",
                    messages=[{"role": "user", "content": "Hi"}],
                ):
                    pass

    @pytest.mark.asyncio
    async def test_stream_completion_api_error(self):
        """Stream completion raises LLMAPIError on API errors."""
        client = LiteLLMClient(api_key="test-key")

        async def raise_api_error(*args, **kwargs):
            raise APIError("Connection refused", request=MagicMock(), body=None)

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=raise_api_error,
        ):
            with pytest.raises(LLMAPIError):
                async for _ in client.stream_completion(
                    model="openai/gpt-4",
                    messages=[{"role": "user", "content": "Hi"}],
                ):
                    pass

    @pytest.mark.asyncio
    async def test_stream_completion_connection_error(self):
        """Stream completion raises LLMAPIError on connection errors."""
        client = LiteLLMClient(api_key="test-key")

        async def raise_connection_error(*args, **kwargs):
            raise APIConnectionError(message="Connection refused", request=MagicMock())

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=raise_connection_error,
        ):
            with pytest.raises(LLMAPIError):
                async for _ in client.stream_completion(
                    model="openai/gpt-4",
                    messages=[{"role": "user", "content": "Hi"}],
                ):
                    pass

    @pytest.mark.asyncio
    async def test_stream_completion_authentication_error(self):
        """Stream completion raises LLMAPIError on authentication errors."""
        client = LiteLLMClient(api_key="test-key")

        async def raise_auth_error(*args, **kwargs):
            raise AuthenticationError(
                "Invalid API key", response=MagicMock(), body=None
            )

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=raise_auth_error,
        ):
            with pytest.raises(LLMAPIError):
                async for _ in client.stream_completion(
                    model="openai/gpt-4",
                    messages=[{"role": "user", "content": "Hi"}],
                ):
                    pass


class TestGetCompletion:
    """Tests for non-streaming completion functionality."""

    @pytest.mark.asyncio
    async def test_get_completion_returns_full_text(self):
        """Get completion collects all chunks and returns full text."""
        client = LiteLLMClient(api_key="test-key")

        mock_chunk_1 = MagicMock()
        mock_chunk_1.choices = [MagicMock(delta=MagicMock(content="Hello "))]
        mock_chunk_2 = MagicMock()
        mock_chunk_2.choices = [MagicMock(delta=MagicMock(content="world"))]

        async def mock_stream_gen():
            for chunk in [mock_chunk_1, mock_chunk_2]:
                yield chunk

        mock_response = mock_stream_gen()

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_completion(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
            )

        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_get_completion_with_system_prompt(self):
        """Get completion accepts system prompt parameter."""
        client = LiteLLMClient(api_key="test-key")

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]

        async def mock_stream_gen():
            yield mock_chunk

        mock_response = mock_stream_gen()

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            await client.get_completion(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="Be concise",
            )

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["messages"][0]["content"] == "Be concise"

    @pytest.mark.asyncio
    async def test_get_completion_empty_response(self):
        """Get completion handles empty response."""
        client = LiteLLMClient(api_key="test-key")

        async def mock_stream_gen():
            return
            yield  # Never reached, but makes this an async generator

        mock_response = mock_stream_gen()

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_completion(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
            )

        assert result == ""

    @pytest.mark.asyncio
    async def test_get_completion_propagates_errors(self):
        """Get completion propagates streaming errors."""
        client = LiteLLMClient(api_key="test-key")

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Request timed out"),
        ):
            with pytest.raises(LLMTimeoutError):
                await client.get_completion(
                    model="invalid/model",
                    messages=[{"role": "user", "content": "Hi"}],
                )


class TestContextManager:
    """Tests for async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_client(self):
        """Context manager properly closes the client."""
        client = LiteLLMClient(api_key="test-key")
        close_mock = AsyncMock()
        client._client.close = close_mock

        async with client as ctx:
            assert ctx is client

        close_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_with_exception(self):
        """Context manager closes client even on exception."""
        client = LiteLLMClient(api_key="test-key")
        close_mock = AsyncMock()
        client._client.close = close_mock

        with pytest.raises(ValueError):
            async with client:
                raise ValueError("Test error")

        close_mock.assert_called_once()


class TestCloseMethod:
    """Tests for explicit close method."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """Close method calls underlying client's close method."""
        client = LiteLLMClient(api_key="test-key")
        close_mock = AsyncMock()
        client._client.close = close_mock

        await client.close()

        close_mock.assert_called_once()


class TestFactoryFunction:
    """Tests for create_llm_client factory function."""

    def test_create_llm_client_with_params(self):
        """Factory creates client with provided parameters."""
        client = create_llm_client(
            api_key="factory-key",
            base_url="https://factory.example.com/",
            timeout=90.0,
        )

        assert isinstance(client, LiteLLMClient)
        assert client.api_key == "factory-key"
        assert client.base_url == "https://factory.example.com/"
        assert client.timeout == 90.0

    def test_create_llm_client_with_env_vars(self, monkeypatch):
        """Factory creates client using environment variables."""
        monkeypatch.setenv("LITELLM_API_KEY", "factory-env-key")

        client = create_llm_client()

        assert isinstance(client, LiteLLMClient)
        assert client.api_key == "factory-env-key"

    def test_create_llm_client_missing_api_key_raises_error(self, monkeypatch):
        """Factory raises error if api_key not available."""
        monkeypatch.delenv("LITELLM_API_KEY", raising=False)

        with pytest.raises(LLMConfigurationError, match="LITELLM_API_KEY"):
            create_llm_client()
