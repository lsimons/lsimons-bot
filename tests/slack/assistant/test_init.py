from unittest.mock import MagicMock, patch

from lsimons_bot.slack.assistant import register


class TestRegister:
    def test_register_happy_path(self) -> None:
        mock_app = MagicMock()
        mock_bot = MagicMock()

        with patch("lsimons_bot.slack.assistant.AsyncAssistant"):
            register(mock_app, mock_bot)
