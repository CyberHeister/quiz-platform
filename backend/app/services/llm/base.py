"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import List

from app.models.quiz import QuizQuestion


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_questions(
        self,
        topic: str,
        difficulty: str,
        count: int,
        question_type: str
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions based on parameters.

        Args:
            topic: Topic for question generation
            difficulty: Difficulty level (easy, medium, hard)
            count: Number of questions to generate
            question_type: Type of questions (single, multi, mixed)

        Returns:
            List of generated QuizQuestion objects

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM provider is available and configured correctly.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'gemini', 'openai')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        pass
