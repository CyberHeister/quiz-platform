"""Quiz question domain model."""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    """A single quiz question with options and answer."""

    id: int = Field(..., ge=1, description="Question number")
    type: Literal["single", "multi"] = Field(
        default="single", description="Question type: single or multi-select"
    )
    question: str = Field(..., min_length=5, max_length=2000, description="Question text")
    options: Dict[str, str] = Field(
        ..., description="Options as {letter: text} mapping, e.g., {'A': 'Option text'}"
    )
    correct_answers: List[str] = Field(
        ..., min_length=1, description="List of correct option letters, e.g., ['B']"
    )
    explanation: Optional[str] = Field(
        default=None, max_length=1000, description="Explanation for the correct answer"
    )

    def validate_options(self) -> bool:
        """Validate that options are properly formatted."""
        if len(self.options) < 2 or len(self.options) > 6:
            return False
        valid_letters = set("ABCDEF")
        for letter in self.options.keys():
            if letter.upper() not in valid_letters:
                return False
        return True

    def validate_correct_answers(self) -> bool:
        """Validate that correct answers reference existing options."""
        option_letters = {k.upper() for k in self.options.keys()}
        for answer in self.correct_answers:
            if answer.upper() not in option_letters:
                return False
        return True
