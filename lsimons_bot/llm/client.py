"""LiteLLM integration module for AI assistant interactions.

Provides a wrapper around the OpenAI SDK configured to work with a LiteLLM proxy,
supporting streaming responses, error handling, and full type annotations.
"""

import logging
import os
from collections.abc import AsyncGenerator
from typing import cast

from openai import (
    APIConnectionError,
    APIError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam

from lsimons_bot.llm.exceptions import (
    LLMAPIError,
    LLMConfigurationError,
    LLMQuotaExceededError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)


class LiteLLMClient:
    """OpenAI client wrapper pointing to LiteLLM proxy.

    Handles streaming, error handling, and environment variable configuration
    for LiteLLM proxy interactions.
    """

    api_key: str
    base_url: str
    timeout: float
    _client: AsyncOpenAI

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        """Initialize LiteLLM client.

        Args:
            api_key: LiteLLM API key. Defaults to LITELLM_API_KEY env var.
            base_url: LiteLLM proxy URL. Defaults to LITELLM_API_BASE env var
                     or https://litellm.sbp.ai/
            timeout: Request timeout in seconds. Defaults to 60.

        Raises:
            LLMConfigurationError: If api_key is not provided or available from environment.
        """
        resolved_api_key = api_key or os.getenv("LITELLM_API_KEY")
        if not resolved_api_key:
            raise LLMConfigurationError("LITELLM_API_KEY must be provided or set as environment variable")
        self.api_key = resolved_api_key

        self.base_url = base_url or os.getenv("LITELLM_API_BASE", "https://litellm.sbp.ai/")
        self.timeout = timeout

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
        )

    async def stream_completion(
        self,
        model: str,
        messages: list[ChatCompletionMessageParam],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from LiteLLM proxy.

        Yields text chunks as they arrive from the streaming response.

        Args:
            model: Model identifier (e.g., "azure/gpt-5-mini", "aws/claude-4-5-sonnet")
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-2.0). Defaults to 0.7.
            max_tokens: Maximum tokens in response. Defaults to None (unlimited).
            system_prompt: Optional system message to prepend to messages.

        Yields:
            Text chunks from the model response.

        Raises:
            LLMConfigurationError: If model configuration is invalid.
            LLMAPIError: If the API request fails.
            LLMTimeoutError: If the request times out.
            LLMQuotaExceededError: If quota or rate limit is exceeded.
        """
        # Prepend system prompt if provided
        request_messages = messages
        if system_prompt:
            request_messages = [
                {"role": "system", "content": system_prompt},
                *messages,
            ]

        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=cast(list[ChatCompletionMessageParam], request_messages),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except TimeoutError as e:
            logger.error(f"LiteLLM timeout for model {model}: {str(e)}")
            raise LLMTimeoutError(f"Request timeout for model {model}") from e
        except RateLimitError as e:
            logger.error(f"LiteLLM quota/rate limit for model {model}: {str(e)}")
            raise LLMQuotaExceededError(f"Quota or rate limit exceeded for model {model}") from e
        except APIConnectionError as e:
            logger.error(f"LiteLLM connection error for model {model}: {str(e)}")
            raise LLMAPIError(f"Connection error for model {model}") from e
        except AuthenticationError as e:
            logger.error(f"LiteLLM authentication error for model {model}: {str(e)}")
            raise LLMAPIError(f"Authentication error for model {model}") from e
        except APIError as e:
            logger.error(f"LiteLLM API error for model {model}: {str(e)}")
            raise LLMAPIError(f"API request failed for model {model}") from e

    async def get_completion(
        self,
        model: str,
        messages: list[ChatCompletionMessageParam],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Get a non-streaming completion from LiteLLM proxy.

        Collects all chunks from the streaming response and returns the full text.

        Args:
            model: Model identifier (e.g., "azure/gpt-5-mini", "aws/claude-4-5-sonnet")
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-2.0). Defaults to 0.7.
            max_tokens: Maximum tokens in response. Defaults to None (unlimited).
            system_prompt: Optional system message to prepend to messages.

        Returns:
            Complete response text from the model.

        Raises:
            LLMConfigurationError: If model configuration is invalid.
            LLMAPIError: If the request fails.
            LLMTimeoutError: If the request times out.
            LLMQuotaExceededError: If quota or rate limit is exceeded.
        """
        response_text = ""
        async for chunk in self.stream_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        ):
            response_text += chunk

        return response_text

    async def close(self) -> None:
        """Close the underlying HTTP client connection."""
        await self._client.close()

    async def __aenter__(self) -> "LiteLLMClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.close()


def create_llm_client(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 60.0,
) -> LiteLLMClient:
    """Factory function to create a configured LiteLLM client.

    Args:
        api_key: LiteLLM API key. Defaults to LITELLM_API_KEY env var.
        base_url: LiteLLM proxy URL. Defaults to LITELLM_API_BASE env var.
        timeout: Request timeout in seconds. Defaults to 60.

    Returns:
        Configured LiteLLMClient instance.

    Raises:
        LLMConfigurationError: If api_key is not provided or available from environment.
    """
    return LiteLLMClient(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
    )
