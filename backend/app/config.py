"""Application configuration via environment variables."""

from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider Configuration
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: Literal["gemini", "openai", "auto"] = "auto"
    # Default model for gemini: gemini-3.6-flash (latest stable for free tier)
    llm_model: Optional[str] = "gemini-3.6-flash"

    # Cache Configuration
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 100

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # Logging
    log_level: str = "INFO"

    # Server
    cors_origins: str = "*"

    @property
    def has_gemini(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.gemini_api_key)

    @property
    def has_openai(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.openai_api_key)

    @property
    def has_any_provider(self) -> bool:
        """Check if at least one LLM provider is configured."""
        return self.has_gemini or self.has_openai

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
