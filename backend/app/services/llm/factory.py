"""Factory for creating LLM provider instances."""

import logging
from typing import Optional

from app.config import Settings, get_settings
from app.exceptions import NoProviderError
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.openai import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating and selecting LLM providers."""

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize factory with settings.

        Args:
            settings: Application settings (uses default if not provided)
        """
        self.settings = settings or get_settings()
        self._providers: dict[str, LLMProvider] = {}

    def _create_gemini_provider(self) -> Optional[GeminiProvider]:
        """Create Gemini provider if configured."""
        if not self.settings.has_gemini:
            return None

        model = self.settings.llm_model or "gemini-1.5-flash"
        return GeminiProvider(
            api_key=self.settings.gemini_api_key,
            model=model
        )

    def _create_openai_provider(self) -> Optional[OpenAIProvider]:
        """Create OpenAI provider if configured."""
        if not self.settings.has_openai:
            return None

        model = self.settings.llm_model
        if model and model.startswith("gemini"):
            model = "gpt-4o-mini"  # Default for OpenAI
        elif not model:
            model = "gpt-4o-mini"

        return OpenAIProvider(
            api_key=self.settings.openai_api_key,
            model=model
        )

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Get an LLM provider instance based on configuration.

        Args:
            provider_name: Specific provider to use (overrides settings)

        Returns:
            LLM provider instance

        Raises:
            NoProviderError: If no provider is configured
        """
        # Determine which provider to use
        if provider_name == "gemini":
            provider = self._create_gemini_provider()
            if provider:
                return provider
            raise NoProviderError()

        elif provider_name == "openai":
            provider = self._create_openai_provider()
            if provider:
                return provider
            raise NoProviderError()

        provider_name = self.settings.llm_provider

        # Explicit Gemini selection
        if provider_name == "gemini":
            provider = self._create_gemini_provider()
            if provider:
                return provider
            raise NoProviderError()

        # Explicit OpenAI selection
        if provider_name == "openai":
            provider = self._create_openai_provider()
            if provider:
                return provider
            raise NoProviderError()

        # Auto mode: try Gemini first, then OpenAI
        provider = self._create_gemini_provider()
        if provider:
            return provider

        provider = self._create_openai_provider()
        if provider:
            return provider

        raise NoProviderError()

    async def get_fallback_provider(self, failed_provider: str) -> Optional[LLMProvider]:
        """
        Get a fallback provider if the primary fails.

        Args:
            failed_provider: Name of the failed provider

        Returns:
            Alternative provider or None if no fallback available
        """
        if failed_provider == "gemini":
            return self._create_openai_provider()
        elif failed_provider == "openai":
            return self._create_gemini_provider()
        return None


def get_llm_factory() -> LLMFactory:
    """Get cached LLM factory instance."""
    return LLMFactory()
