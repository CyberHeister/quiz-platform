"""Quiz generation API routes."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.exceptions import NoProviderError, QuizPlatformError, RateLimitError
from app.models import QuizGenerateRequest, QuizGenerateResponse, HealthResponse
from app.services.cache import get_cache
from app.services.generator import QuizGenerator, get_generator
from app.services.llm.factory import LLMFactory, get_llm_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post(
    "/generate",
    response_model=QuizGenerateResponse,
    summary="Generate quiz questions",
    description="Generate multiple-choice questions on a given topic using web scraping and/or LLM"
)
async def generate_quiz(
    request: QuizGenerateRequest,
    generator: QuizGenerator = Depends(get_generator)
) -> QuizGenerateResponse:
    """
    Generate quiz questions.

    Attempts to find real MCQs via web scraping first,
    then falls back to LLM generation if needed.
    """
    try:
        logger.info(
            f"Generating quiz: topic='{request.topic[:30]}...', "
            f"difficulty={request.difficulty}, count={request.count}, type={request.question_type}"
        )

        questions, metadata = await generator.generate(
            topic=request.topic,
            difficulty=request.difficulty,
            count=request.count,
            question_type=request.question_type
        )

        return QuizGenerateResponse(
            success=True,
            questions=questions,
            metadata=metadata
        )

    except NoProviderError as e:
        logger.error(f"No LLM provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": e.code,
                "message": e.message
            }
        )

    except QuizPlatformError as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": e.code,
                "message": e.message
            }
        )

    except Exception as e:
        logger.exception(f"Unexpected error during quiz generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API health status and provider availability"
)
async def health_check(
    llm_factory: LLMFactory = Depends(get_llm_factory),
    cache = Depends(get_cache)
) -> HealthResponse:
    """Check system health and provider status."""
    providers = {}

    # Check Gemini
    try:
        gemini = llm_factory._create_gemini_provider()
        if gemini:
            providers["gemini"] = await gemini.health_check()
        else:
            providers["gemini"] = False
    except Exception:
        providers["gemini"] = False

    # Check OpenAI
    try:
        openai = llm_factory._create_openai_provider()
        if openai:
            providers["openai"] = await openai.health_check()
        else:
            providers["openai"] = False
    except Exception:
        providers["openai"] = False

    # Determine overall status
    any_healthy = any(providers.values())
    all_healthy = all(providers.values()) if providers else False

    if all_healthy:
        status_val = "healthy"
    elif any_healthy:
        status_val = "degraded"
    else:
        status_val = "unhealthy"

    return HealthResponse(
        status=status_val,
        providers=providers,
        cache=cache.get_stats()
    )
