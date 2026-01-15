from unittest.mock import MagicMock, patch

from lsimons_bot.slack.assistant import register


class TestRegister:
    def test_register_happy_path(self) -> None:
        mock_app = MagicMock()
        mock_bot = MagicMock()

        with patch("lsimons_bot.slack.assistant.AsyncAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            with patch("lsimons_bot.slack.assistant.assistant_message_handler_maker") as mock_factory:
                mock_handler = MagicMock()
                mock_factory.return_value = mock_handler

                register(mock_app, mock_bot)

                # Verify the factory was called with the bot instance
                mock_factory.assert_called_once_with(mock_bot)

                # Verify assistant methods were called properly
                mock_assistant.thread_started.assert_called_once()
                mock_assistant.user_message.assert_called_once_with(mock_handler)

                # Verify the assistant was registered with the app
                mock_app.use.assert_called_once_with(mock_assistant)
