"""LLM module exceptions."""


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


class LLMConfigurationError(LLMError):
    """Raised when LLM configuration is invalid or missing."""

    pass


class LLMAPIError(LLMError):
    """Raised when LLM API request fails."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM API request times out."""

    pass


class LLMQuotaExceededError(LLMError):
    """Raised when LLM quota or rate limit is exceeded."""

    pass
