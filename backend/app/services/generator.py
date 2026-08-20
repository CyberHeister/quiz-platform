"""Quiz generation orchestrator service."""

import logging
from datetime import datetime
from typing import List, Optional

from app.config import Settings, get_settings
from app.exceptions import NoProviderError, QuizPlatformError
from app.models.quiz import QuizQuestion
from app.models.responses import QuizMetadata
from app.services.cache import QuizCache, get_cache
from app.services.llm.base import LLMProvider
from app.services.llm.factory import LLMFactory, get_llm_factory
from app.services.scraping.duckduckgo import DuckDuckGoScraper

logger = logging.getLogger(__name__)


class QuizGenerator:
    """Orchestrates quiz generation from scraping and LLM sources."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        cache: Optional[QuizCache] = None,
        llm_factory: Optional[LLMFactory] = None
    ):
        """
        Initialize the quiz generator.

        Args:
            settings: Application settings
            cache: Response cache
            llm_factory: LLM provider factory
        """
        self.settings = settings or get_settings()
        self.cache = cache or get_cache()
        self.llm_factory = llm_factory or get_llm_factory()
        self._scraper = None

    def _get_scraper(self) -> Optional[DuckDuckGoScraper]:
        """Get or create the web scraper."""
        if self._scraper is None:
            try:
                self._scraper = DuckDuckGoScraper(max_results=5)
            except Exception as e:
                logger.warning(f"Failed to initialize scraper: {e}")
        return self._scraper

    async def _try_fallback_provider(
        self,
        original_error: Exception,
        topic: str,
        difficulty: str,
        count: int,
        question_type: str
    ) -> List[QuizQuestion]:
        """Try fallback provider when primary fails with quota error."""
        try:
            # Determine which provider was primary from the original error
            error_str = str(original_error).lower()
            primary = "openai" if "openai" in error_str else "gemini"
            fallback = self.llm_factory._create_gemini_provider() if primary == "openai" else self.llm_factory._create_openai_provider()

            if fallback:
                logger.info(f"Trying fallback provider: {fallback.provider_name}")
                questions = await fallback.generate_questions(
                    topic=topic,
                    difficulty=difficulty,
                    count=count,
                    question_type=question_type
                )
                return questions
        except Exception as e:
            logger.error(f"Fallback provider also failed: {e}")
        return []

    async def generate(
        self,
        topic: str,
        difficulty: str,
        count: int,
        question_type: str,
        skip_cache: bool = False
    ) -> tuple[List[QuizQuestion], QuizMetadata]:
        """
        Generate quiz questions.

        First attempts to find real MCQs via web scraping,
        then falls back to LLM generation if needed.

        Args:
            topic: Topic for questions
            difficulty: Difficulty level (easy, medium, hard)
            count: Number of questions
            question_type: Type (single, multi, mixed)
            skip_cache: Skip cache lookup

        Returns:
            Tuple of (questions list, metadata)

        Raises:
            QuizPlatformError: If generation fails
        """
        # Check cache first
        if not skip_cache:
            cached = self.cache.get(topic, difficulty, count, question_type)
            if cached:
                metadata = QuizMetadata(
                    provider=cached["metadata"]["provider"],
                    model=cached["metadata"]["model"],
                    source=cached["metadata"]["source"],
                    cached=True,
                    generated_at=datetime.fromisoformat(cached["metadata"]["generated_at"])
                )
                return cached["questions"], metadata

        questions = []
        source = "llm"
        provider_name = "unknown"
        model_name = "unknown"

        # Step 1: Try web scraping
        scraper = self._get_scraper()
        if scraper:
            try:
                scraped_questions = await scraper.search_questions(topic, count)
                if len(scraped_questions) >= count:
                    # Found enough questions via scraping
                    questions = scraped_questions[:count]
                    source = "scraping"
                    provider_name = scraper.scraper_name
                    model_name = "n/a"
                    logger.info(f"Got {len(questions)} questions via scraping")
            except Exception as e:
                logger.warning(f"Scraping failed: {e}")

        # Step 2: Fall back to LLM if scraping didn't find enough
        if len(questions) < count:
            remaining = count - len(questions)

            try:
                provider = self.llm_factory.get_provider()
                provider_name = provider.provider_name
                model_name = provider.model_name

                llm_questions = await provider.generate_questions(
                    topic=topic,
                    difficulty=difficulty,
                    count=remaining,
                    question_type=question_type
                )

                # Add LLM questions (continue numbering)
                start_id = len(questions) + 1
                for i, q in enumerate(llm_questions):
                    q.id = start_id + i
                    questions.append(q)

                source = "llm"

            except NoProviderError:
                if not questions:
                    raise
                # If we have some scraped questions, continue with those
                logger.warning("No LLM provider available, using scraped questions only")

            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                # Check for quota/rate limit errors - try fallback provider
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                    logger.warning("Primary provider quota exceeded, trying fallback...")
                    fallback = await self._try_fallback_provider(
                        e, topic, difficulty, count - len(questions), question_type
                    )
                    if fallback:
                        questions.extend(fallback)
                        source = "llm"
                        continue

                if not questions:
                    if "429" in error_str or "quota" in error_str:
                        raise QuizPlatformError(
                            "API quota exceeded. Please add a Gemini API key or upgrade your OpenAI plan.",
                            code="QUOTA_EXCEEDED"
                        )
                    raise QuizPlatformError(
                        f"Failed to generate questions: {str(e)}"
                    )

        # Final validation
        if not questions:
            raise QuizPlatformError("No questions could be generated")

        # Create metadata
        metadata = QuizMetadata(
            provider=provider_name,
            model=model_name,
            source=source,
            cached=False,
            generated_at=datetime.utcnow()
        )

        # Cache the result
        self.cache.set(
            topic, difficulty, count, question_type,
            {
                "questions": [q.model_dump() for q in questions],
                "metadata": metadata.model_dump()
            }
        )

        return questions, metadata


# Global generator instance
_generator: Optional[QuizGenerator] = None


def get_generator() -> QuizGenerator:
    """Get the global quiz generator instance."""
    global _generator
    if _generator is None:
        _generator = QuizGenerator()
    return _generator
