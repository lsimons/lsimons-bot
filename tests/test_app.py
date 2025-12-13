from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lsimons_bot.app import main


class TestMain:
    @pytest.mark.asyncio
    async def test_main_happy_path(self) -> None:
        """Test that main initializes and starts the Slack app successfully."""
        mock_env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_APP_TOKEN": "xapp-test-token",
        }

        with (
            patch("lsimons_bot.app.get_env_vars", return_value=mock_env_vars),
            patch("lsimons_bot.app.AsyncApp"),
            patch("lsimons_bot.app.assistant.register"),
            patch("lsimons_bot.app.messages.register"),
            patch("lsimons_bot.app.home.register"),
            patch("lsimons_bot.app.AsyncSocketModeHandler") as mock_handler_class,
        ):
            mock_handler = MagicMock()
            mock_handler.start_async = AsyncMock()
            mock_handler_class.return_value = mock_handler

            await main()
