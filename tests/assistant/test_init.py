from unittest.mock import MagicMock, patch

from lsimons_bot.assistant import register


class TestRegister:
    def test_register_happy_path(self) -> None:
        """Test that register runs without error."""
        mock_app = MagicMock()

        with patch("lsimons_bot.assistant.AsyncAssistant"):
            register(mock_app)
