"""In-memory response cache for quiz generation."""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class QuizCache:
    """Thread-safe TTL cache for quiz responses."""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 100):
        """
        Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for cached items in seconds
            max_size: Maximum number of items to cache
        """
        self._cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self._hits = 0
        self._misses = 0

    def _generate_key(self, topic: str, difficulty: str, count: int, question_type: str) -> str:
        """Generate a cache key from request parameters."""
        key_string = f"{topic}|{difficulty}|{count}|{question_type}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self,
        topic: str,
        difficulty: str,
        count: int,
        question_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available.

        Args:
            topic: Quiz topic
            difficulty: Difficulty level
            count: Number of questions
            question_type: Type of questions

        Returns:
            Cached response dict or None
        """
        key = self._generate_key(topic, difficulty, count, question_type)

        try:
            if key in self._cache:
                self._hits += 1
                logger.debug(f"Cache hit for: {topic[:30]}...")
                return self._cache[key]
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        self._misses += 1
        return None

    def set(
        self,
        topic: str,
        difficulty: str,
        count: int,
        question_type: str,
        response: Dict[str, Any]
    ) -> None:
        """
        Store response in cache.

        Args:
            topic: Quiz topic
            difficulty: Difficulty level
            count: Number of questions
            question_type: Type of questions
            response: Response dict to cache
        """
        key = self._generate_key(topic, difficulty, count, question_type)

        try:
            self._cache[key] = response
            logger.debug(f"Cached response for: {topic[:30]}...")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._cache.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
        }


# Global cache instance
_cache: Optional[QuizCache] = None


def get_cache() -> QuizCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        from app.config import get_settings
        settings = get_settings()
        _cache = QuizCache(
            ttl_seconds=settings.cache_ttl_seconds,
            max_size=settings.cache_max_size
        )
    return _cache
