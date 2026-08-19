"""Abstract base class for web scrapers."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.quiz import QuizQuestion


class MCQScraper(ABC):
    """Abstract interface for MCQ scrapers."""

    @abstractmethod
    async def search_questions(
        self,
        topic: str,
        count: int = 10
    ) -> List[QuizQuestion]:
        """
        Search for MCQs on the given topic.

        Args:
            topic: Topic to search for
            count: Maximum number of questions to return

        Returns:
            List of found QuizQuestion objects (may be empty)
        """
        pass

    @property
    @abstractmethod
    def scraper_name(self) -> str:
        """Return the scraper name."""
        pass
