"""Google Gemini LLM provider implementation."""

import json
import logging
from typing import List

from app.exceptions import LLMProviderError
from app.models.quiz import QuizQuestion
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)

GEMINI_PROMPT_TEMPLATE = """Generate {count} multiple-choice quiz questions about "{topic}" at {difficulty} difficulty level.

Requirements:
1. Question type: {question_type_instruction}
2. Each question must have exactly 4 options labeled A, B, C, D
3. For single-select questions, exactly one correct answer
4. For multi-select questions, 2-4 correct answers
5. Include a brief explanation (1-2 sentences) for each correct answer
6. Make questions clear, unambiguous, and educational
7. Difficulty levels:
   - easy: basic concepts, straightforward answers
   - medium: intermediate concepts, some analysis required
   - hard: advanced concepts, requires deep understanding

Return ONLY a valid JSON array with this exact format:
[
  {{
    "id": 1,
    "type": "single",
    "question": "Question text here?",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "correct_answers": ["B"],
    "explanation": "Brief explanation of why B is correct"
  }}
]

IMPORTANT: The "type" field MUST be exactly "single" or "multi" (lowercase). Do NOT use "multiple", "single-select", "multi-select", or any other variation.

Generate {count} questions now:"""


class GeminiProvider(LLMProvider):
    """Google Gemini API provider for quiz generation."""

    def __init__(self, api_key: str, model: str = "gemini-3.6-flash"):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google Gemini API key
            model: Model identifier (default: gemini-3.6-flash)
        """
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        """Lazy-load the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._client = genai.GenerativeModel(self._model)
            except ImportError:
                raise LLMProviderError(
                    "google-generativeai package not installed. Run: pip install google-generativeai",
                    provider="gemini"
                )
        return self._client

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def _get_question_type_instruction(self, question_type: str) -> str:
        """Get instruction text for question type."""
        if question_type == "single":
            return "All questions should be single-select (one correct answer)"
        elif question_type == "multi":
            return "All questions should be multi-select (multiple correct answers)"
        else:  # mixed
            return "Mix of single-select and multi-select questions"

    async def generate_questions(
        self,
        topic: str,
        difficulty: str,
        count: int,
        question_type: str
    ) -> List[QuizQuestion]:
        """Generate quiz questions using Gemini API."""
        prompt = GEMINI_PROMPT_TEMPLATE.format(
            count=count,
            topic=topic,
            difficulty=difficulty,
            question_type_instruction=self._get_question_type_instruction(question_type)
        )

        try:
            client = self._get_client()
            response = await client.generate_content_async(prompt)

            if not response or not response.text:
                raise LLMProviderError(
                    "Empty response from Gemini API",
                    provider="gemini"
                )

            # Parse JSON from response
            text = response.text.strip()

            # Extract JSON array from response (handle markdown code blocks)
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            questions_data = json.loads(text.strip())

            # Validate and convert to QuizQuestion objects
            questions = []
            for i, q in enumerate(questions_data[:count], start=1):
                question = QuizQuestion(
                    id=q.get("id", i),
                    type=q.get("type", "single"),
                    question=q["question"],
                    options=q["options"],
                    correct_answers=q["correct_answers"],
                    explanation=q.get("explanation")
                )

                # Validate
                if not question.validate_options():
                    logger.warning(f"Invalid options in question {i}, skipping")
                    continue
                if not question.validate_correct_answers():
                    logger.warning(f"Invalid correct answers in question {i}, skipping")
                    continue

                questions.append(question)

            if not questions:
                raise LLMProviderError(
                    "No valid questions generated",
                    provider="gemini"
                )

            logger.info(f"Generated {len(questions)} questions via Gemini")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise LLMProviderError(
                f"Failed to parse LLM response: {str(e)}",
                provider="gemini"
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise LLMProviderError(
                f"Gemini API error: {str(e)}",
                provider="gemini"
            )

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            client = self._get_client()
            # Simple test generation
            response = await client.generate_content_async("Say 'OK' if you can read this.")
            return bool(response and response.text)
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False
