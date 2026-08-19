"""Request models for API endpoints."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class QuizGenerateRequest(BaseModel):
    """Request model for quiz generation endpoint."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Topic for quiz generation, e.g., 'AWS S3 storage fundamentals'"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        default="medium",
        description="Question difficulty level"
    )
    count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of questions to generate (1-50)"
    )
    question_type: Literal["single", "multi", "mixed"] = Field(
        default="mixed",
        description="Type of questions: single-select, multi-select, or mixed"
    )

    @field_validator("topic")
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        """Sanitize topic input to prevent injection."""
        # Remove potentially dangerous characters but allow common punctuation
        sanitized = "".join(c for c in v if c.isalnum() or c in " -_,./()&")
        return sanitized.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AWS S3 storage fundamentals",
                "difficulty": "medium",
                "count": 10,
                "question_type": "mixed"
            }
        }
