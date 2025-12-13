from collections.abc import AsyncIterator, Iterable

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam


class LLMClient:
    client: AsyncOpenAI
    model: str

    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4") -> None:
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    async def chat_completion_stream(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def chat_completion(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content

        return ""
