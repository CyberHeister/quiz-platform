"""OpenAI LLM provider implementation."""

import json
import logging
from typing import List

from app.exceptions import LLMProviderError
from app.models.quiz import QuizQuestion
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)

OPENAI_PROMPT_TEMPLATE = """Generate {count} multiple-choice quiz questions about "{topic}" at {difficulty} difficulty level.

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

Generate {count} questions now:"""


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for quiz generation."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model identifier (default: gpt-4o-mini for cost efficiency)
        """
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except ImportError:
                raise LLMProviderError(
                    "openai package not installed. Run: pip install openai",
                    provider="openai"
                )
        return self._client

    @property
    def provider_name(self) -> str:
        return "openai"

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
        """Generate quiz questions using OpenAI API."""
        prompt = OPENAI_PROMPT_TEMPLATE.format(
            count=count,
            topic=topic,
            difficulty=difficulty,
            question_type_instruction=self._get_question_type_instruction(question_type)
        )

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert quiz question generator. Generate high-quality, educational multiple-choice questions. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise LLMProviderError(
                    "Empty response from OpenAI API",
                    provider="openai"
                )

            content = response.choices[0].message.content
            if not content:
                raise LLMProviderError(
                    "Empty content in OpenAI response",
                    provider="openai"
                )

            # Parse JSON from response
            data = json.loads(content)

            # Handle both direct array and wrapped object
            if isinstance(data, dict):
                questions_data = data.get("questions", data.get("quiz", []))
            else:
                questions_data = data

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
                    provider="openai"
                )

            logger.info(f"Generated {len(questions)} questions via OpenAI")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise LLMProviderError(
                f"Failed to parse LLM response: {str(e)}",
                provider="openai"
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMProviderError(
                f"OpenAI API error: {str(e)}",
                provider="openai"
            )

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5
            )
            return bool(response and response.choices)
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
