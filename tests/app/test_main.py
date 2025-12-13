from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lsimons_bot.app.main import main


class TestMain:
    @pytest.mark.asyncio
    async def test_main_happy_path(self) -> None:
        mock_env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_APP_TOKEN": "xapp-test-token",
            "OPENAI_BASE_URL": "http://localhost:8000",
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL": "gpt-4",
        }

        with (
            patch("lsimons_bot.app.main.get_env_vars", return_value=mock_env_vars),
            patch("lsimons_bot.app.main.LLMClient"),
            patch("lsimons_bot.app.main.AsyncApp"),
            patch("lsimons_bot.app.main.assistant.register"),
            patch("lsimons_bot.app.main.messages.register"),
            patch("lsimons_bot.app.main.home.register"),
            patch("lsimons_bot.app.main.AsyncSocketModeHandler") as mock_handler_class,
        ):
            mock_handler = MagicMock()
            mock_handler.start_async = AsyncMock()
            mock_handler_class.return_value = mock_handler

            await main()
