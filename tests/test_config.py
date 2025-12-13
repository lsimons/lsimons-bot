import os
from unittest.mock import patch

import pytest

from lsimons_bot.config import get_env_vars, validate_env_vars


class TestValidateEnvVars:
    def test_all_variables_present(self) -> None:
        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}, clear=True):
            result = validate_env_vars(["VAR1", "VAR2"])
            assert result == {"VAR1": "value1", "VAR2": "value2"}

    def test_missing_variables(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(match="Missing required environment variables"):
                validate_env_vars(["VAR1", "VAR2"])


class TestGetEnvVars:
    def test_all_env_vars_present(self) -> None:
        with patch.dict(
            os.environ,
            {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_APP_TOKEN": "xapp-test"},
            clear=True,
        ):
            result = get_env_vars()
            assert result == {
                "SLACK_BOT_TOKEN": "xoxb-test",
                "SLACK_APP_TOKEN": "xapp-test",
            }

    def test_missing_env_vars(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(match="Missing required environment variables"):
                get_env_vars()
