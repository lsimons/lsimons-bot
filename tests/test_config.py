"""Tests for configuration and environment variable validation."""

import os
from unittest.mock import patch

import pytest

from lsimons_bot.config import (
    ConfigurationError,
    get_oauth_env_vars,
    get_socket_mode_env_vars,
    validate_env_vars,
)


class TestValidateEnvVars:
    """Tests for validate_env_vars function."""

    def test_all_variables_present(self) -> None:
        """Test validation succeeds when all variables are present."""
        with patch.dict(
            os.environ,
            {"VAR1": "value1", "VAR2": "value2", "VAR3": "value3"},
            clear=True,
        ):
            result = validate_env_vars(["VAR1", "VAR2", "VAR3"])
            assert result == {"VAR1": "value1", "VAR2": "value2", "VAR3": "value3"}

    def test_missing_single_variable(self) -> None:
        """Test validation fails when a single variable is missing."""
        with patch.dict(os.environ, {"VAR1": "value1"}, clear=True):
            with pytest.raises(ConfigurationError, match="Missing required environment variables: VAR2"):
                validate_env_vars(["VAR1", "VAR2"])

    def test_missing_multiple_variables(self) -> None:
        """Test validation fails when multiple variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: VAR1, VAR2, VAR3",
            ):
                validate_env_vars(["VAR1", "VAR2", "VAR3"])

    def test_empty_string_treated_as_missing(self) -> None:
        """Test that empty string values are treated as missing."""
        with patch.dict(os.environ, {"VAR1": ""}, clear=True):
            with pytest.raises(ConfigurationError, match="Missing required environment variables: VAR1"):
                validate_env_vars(["VAR1"])

    def test_empty_list(self) -> None:
        """Test validation with no required variables."""
        result = validate_env_vars([])
        assert result == {}


class TestGetSocketModeEnvVars:
    """Tests for get_socket_mode_env_vars function."""

    def test_all_socket_mode_vars_present(self) -> None:
        """Test retrieval succeeds when all socket mode variables are present."""
        with patch.dict(
            os.environ,
            {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_APP_TOKEN": "xapp-test"},
            clear=True,
        ):
            result = get_socket_mode_env_vars()
            assert result == {
                "SLACK_BOT_TOKEN": "xoxb-test",
                "SLACK_APP_TOKEN": "xapp-test",
            }

    def test_missing_slack_bot_token(self) -> None:
        """Test failure when SLACK_BOT_TOKEN is missing."""
        with patch.dict(os.environ, {"SLACK_APP_TOKEN": "xapp-test"}, clear=True):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: SLACK_BOT_TOKEN",
            ):
                get_socket_mode_env_vars()

    def test_missing_slack_app_token(self) -> None:
        """Test failure when SLACK_APP_TOKEN is missing."""
        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test"}, clear=True):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: SLACK_APP_TOKEN",
            ):
                get_socket_mode_env_vars()

    def test_missing_all_socket_mode_vars(self) -> None:
        """Test failure when all socket mode variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: SLACK_BOT_TOKEN, SLACK_APP_TOKEN",
            ):
                get_socket_mode_env_vars()


class TestGetOAuthEnvVars:
    """Tests for get_oauth_env_vars function."""

    def test_all_oauth_vars_present(self) -> None:
        """Test retrieval succeeds when all OAuth variables are present."""
        with patch.dict(
            os.environ,
            {
                "SLACK_SIGNING_SECRET": "secret123",
                "SLACK_CLIENT_ID": "client123",
                "SLACK_CLIENT_SECRET": "clientsecret123",
            },
            clear=True,
        ):
            result = get_oauth_env_vars()
            assert result == {
                "SLACK_SIGNING_SECRET": "secret123",
                "SLACK_CLIENT_ID": "client123",
                "SLACK_CLIENT_SECRET": "clientsecret123",
            }

    def test_missing_slack_signing_secret(self) -> None:
        """Test failure when SLACK_SIGNING_SECRET is missing."""
        with patch.dict(
            os.environ,
            {"SLACK_CLIENT_ID": "client123", "SLACK_CLIENT_SECRET": "clientsecret123"},
            clear=True,
        ):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: SLACK_SIGNING_SECRET",
            ):
                get_oauth_env_vars()

    def test_missing_slack_client_id(self) -> None:
        """Test failure when SLACK_CLIENT_ID is missing."""
        with patch.dict(
            os.environ,
            {
                "SLACK_SIGNING_SECRET": "secret123",
                "SLACK_CLIENT_SECRET": "clientsecret123",
            },
            clear=True,
        ):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: SLACK_CLIENT_ID",
            ):
                get_oauth_env_vars()

    def test_missing_slack_client_secret(self) -> None:
        """Test failure when SLACK_CLIENT_SECRET is missing."""
        with patch.dict(
            os.environ,
            {"SLACK_SIGNING_SECRET": "secret123", "SLACK_CLIENT_ID": "client123"},
            clear=True,
        ):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: SLACK_CLIENT_SECRET",
            ):
                get_oauth_env_vars()

    def test_missing_all_oauth_vars(self) -> None:
        """Test failure when all OAuth variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ConfigurationError,
                match="Missing required environment variables: SLACK_SIGNING_SECRET, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET",
            ):
                get_oauth_env_vars()
