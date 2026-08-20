"""Response models for API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.quiz import QuizQuestion


class QuizMetadata(BaseModel):
    """Metadata about quiz generation."""

    provider: str = Field(..., description="LLM provider used: gemini or openai")
    model: str = Field(..., description="Model identifier used")
    source: Literal["llm", "scraping"] = Field(..., description="Source of questions")
    cached: bool = Field(default=False, description="Whether response was cached")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of generation"
    )


class ErrorDetail(BaseModel):
    """Error details for API responses."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    retry_after: Optional[int] = Field(
        default=None, description="Seconds to wait before retry (for rate limits)"
    )


class QuizGenerateResponse(BaseModel):
    """Response model for quiz generation endpoint."""

    success: bool = Field(..., description="Whether generation was successful")
    questions: Optional[List[QuizQuestion]] = Field(
        default=None, description="Generated quiz questions"
    )
    metadata: Optional[QuizMetadata] = Field(
        default=None, description="Generation metadata"
    )
    error: Optional[ErrorDetail] = Field(
        default=None, description="Error details if failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "questions": [
                    {
                        "id": 1,
                        "type": "single",
                        "question": "Which AWS service is used to run code without provisioning servers?",
                        "options": {
                            "A": "EC2",
                            "B": "Lambda",
                            "C": "S3",
                            "D": "RDS"
                        },
                        "correct_answers": ["B"],
                        "explanation": "AWS Lambda is a serverless compute service."
                    }
                ],
                "metadata": {
                    "provider": "gemini",
                    "model": "gemini-3.6-flash",
                    "source": "llm",
                    "cached": False,
                    "generated_at": "2026-08-19T13:00:00Z"
                }
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall health status"
    )
    providers: Dict[str, bool] = Field(
        ..., description="Status of each LLM provider"
    )
    cache: Dict[str, Any] = Field(
        ..., description="Cache statistics"
    )
    version: str = Field(default="1.0.0", description="API version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "providers": {
                    "gemini": True,
                    "openai": False
                },
                "cache": {
                    "size": 15,
                    "max_size": 100,
                    "hits": 42,
                    "misses": 15
                },
                "version": "1.0.0"
            }
        }
