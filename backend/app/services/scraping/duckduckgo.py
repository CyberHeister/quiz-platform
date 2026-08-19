"""DuckDuckGo search scraper for MCQ discovery."""

import json
import logging
import re
from typing import List, Optional

from app.models.quiz import QuizQuestion
from app.services.scraping.base import MCQScraper

logger = logging.getLogger(__name__)


class DuckDuckGoScraper(MCQScraper):
    """DuckDuckGo-based MCQ scraper."""

    def __init__(self, max_results: int = 5):
        """
        Initialize DuckDuckGo scraper.

        Args:
            max_results: Maximum number of search results to process
        """
        self._max_results = max_results
        self._client = None

    def _get_client(self):
        """Lazy-load the DuckDuckGo search client."""
        if self._client is None:
            try:
                from duckduckgo_search import DDGS
                self._client = DDGS()
            except ImportError:
                logger.warning("duckduckgo-search not installed")
                return None
        return self._client

    @property
    def scraper_name(self) -> str:
        return "duckduckgo"

    def _extract_mcq_pattern(self, text: str) -> List[dict]:
        """
        Extract MCQ questions from text using pattern matching.

        Args:
            text: Raw text to parse

        Returns:
            List of question dictionaries
        """
        questions = []

        # Pattern for numbered questions with options
        # Matches: "1. Question text?\nA. Option\nB. Option\nC. Option\nD. Option"
        q_pattern = r'(\d+)[\.\)]\s*(.+?)(?=\n[A-D][\.\)]|\nAnswer|\nCorrect|$)'
        opt_pattern = r'([A-D])[\.\)]\s*(.+?)(?=\n[A-D][\.\)]|\nAnswer|\nCorrect|\n\d+[\.\)]|$)'
        ans_pattern = r'(?:Answer|Correct\s*Answer?)\s*[:\-]?\s*([A-D])'

        # Find all question blocks
        blocks = re.split(r'\n(?=\d+[\.\)])', text)

        for block in blocks[:20]:  # Limit processing
            if not block.strip():
                continue

            # Extract question number and text
            q_match = re.match(r'(\d+)[\.\)]\s*(.+?)(?=\n[A-D][\.\)])', block, re.DOTALL)
            if not q_match:
                continue

            q_num = int(q_match.group(1))
            q_text = q_match.group(2).strip()

            # Extract options
            options = {}
            for opt_match in re.finditer(opt_pattern, block, re.MULTILINE):
                letter = opt_match.group(1)
                opt_text = opt_match.group(2).strip()
                if opt_text and len(opt_text) > 1:
                    options[letter] = opt_text[:200]  # Limit option length

            # Need at least 2 options
            if len(options) < 2:
                continue

            # Extract correct answer
            ans_match = re.search(ans_pattern, block, re.IGNORECASE)
            correct = [ans_match.group(1)] if ans_match else []

            if q_text and options:
                questions.append({
                    "id": q_num,
                    "question": q_text[:500],  # Limit question length
                    "options": options,
                    "correct_answers": correct,
                    "type": "single"
                })

        return questions

    async def search_questions(
        self,
        topic: str,
        count: int = 10
    ) -> List[QuizQuestion]:
        """Search for MCQs using DuckDuckGo."""
        client = self._get_client()
        if not client:
            return []

        try:
            # Search for MCQs on the topic
            search_query = f"{topic} multiple choice questions MCQ"

            results = client.text(
                search_query,
                max_results=self._max_results
            )

            if not results:
                logger.info(f"No search results for: {topic}")
                return []

            all_questions = []

            for result in results:
                # Try to extract MCQs from the snippet
                snippet = result.get("body", "")
                if not snippet:
                    continue

                extracted = self._extract_mcq_pattern(snippet)
                all_questions.extend(extracted)

            # Convert to QuizQuestion objects
            questions = []
            for i, q in enumerate(all_questions[:count], start=1):
                try:
                    question = QuizQuestion(
                        id=q.get("id", i),
                        type=q.get("type", "single"),
                        question=q["question"],
                        options=q["options"],
                        correct_answers=q.get("correct_answers", [])
                    )

                    # Validate
                    if not question.validate_options():
                        continue
                    if not question.correct_answers:
                        continue  # Skip questions without answers

                    questions.append(question)

                except Exception as e:
                    logger.warning(f"Failed to create question: {e}")
                    continue

            logger.info(f"Scraped {len(questions)} questions for topic: {topic}")
            return questions

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
