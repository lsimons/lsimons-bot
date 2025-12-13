"""Configuration and environment variable validation for Slack bot.

Provides utilities to validate required environment variables and raise clear
errors if any are missing.
"""

import os


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


def validate_env_vars(required_vars: list[str]) -> dict[str, str]:
    """Validate that all required environment variables are set.

    Args:
        required_vars: List of environment variable names that must be set.

    Returns:
        Dictionary mapping variable names to their values.

    Raises:
        ConfigurationError: If any required environment variable is missing.
    """
    missing_vars: list[str] = []
    env_values: dict[str, str] = {}

    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            env_values[var] = value

    if missing_vars:
        raise ConfigurationError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return env_values


def get_socket_mode_env_vars() -> dict[str, str]:
    """Validate and retrieve environment variables for socket mode app.

    Returns:
        Dictionary with SLACK_BOT_TOKEN and SLACK_APP_TOKEN values.

    Raises:
        ConfigurationError: If required variables are missing.
    """
    return validate_env_vars(["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"])


def get_oauth_env_vars() -> dict[str, str]:
    """Validate and retrieve environment variables for OAuth app.

    Returns:
        Dictionary with SLACK_SIGNING_SECRET, SLACK_CLIENT_ID, and
        SLACK_CLIENT_SECRET values.

    Raises:
        ConfigurationError: If required variables are missing.
    """
    return validate_env_vars(["SLACK_SIGNING_SECRET", "SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"])
