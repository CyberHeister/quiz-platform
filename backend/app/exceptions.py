"""Custom exceptions for the quiz platform."""


class QuizPlatformError(Exception):
    """Base exception for quiz platform errors."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(QuizPlatformError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class LLMProviderError(QuizPlatformError):
    """Raised when LLM provider fails."""

    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(message, "LLM_PROVIDER_ERROR")


class ScrapingError(QuizPlatformError):
    """Raised when web scraping fails."""

    def __init__(self, message: str):
        super().__init__(message, "SCRAPING_ERROR")


class RateLimitError(QuizPlatformError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds.",
            "RATE_LIMIT_EXCEEDED"
        )


class NoProviderError(QuizPlatformError):
    """Raised when no LLM provider is configured."""

    def __init__(self):
        super().__init__(
            "No LLM provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY.",
            "NO_PROVIDER_CONFIGURED"
        )
