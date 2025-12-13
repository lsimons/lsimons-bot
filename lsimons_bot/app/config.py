import os

REQUIRED_VARS = [
    "SLACK_BOT_TOKEN",
    "SLACK_APP_TOKEN",
    "OPENAI_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
]


def validate_env_vars(required_vars: list[str]) -> dict[str, str]:
    missing_vars: list[str] = []
    env_values: dict[str, str] = {}

    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            env_values[var] = value

    if missing_vars:
        raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

    return env_values


def get_env_vars() -> dict[str, str]:
    return validate_env_vars(REQUIRED_VARS)
