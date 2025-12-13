from unittest.mock import MagicMock

import pytest

from lsimons_bot.home import register
from lsimons_bot.home.app_home_opened import app_home_opened


class TestRegister:
    def test_register_happy_path(self) -> None:
        mock_app = MagicMock()
        mock_event = MagicMock()
        mock_app.event.return_value = mock_event

        register(mock_app)

        mock_app.event.assert_called_once_with("app_home_opened")


class TestAppHomeOpened:
    @pytest.mark.asyncio
    async def test_app_home_opened_runs_without_error(self) -> None:
        await app_home_opened()
