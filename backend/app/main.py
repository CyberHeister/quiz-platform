"""FastAPI application entry point with Mangum handler for Lambda."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import quiz
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()

    # Startup
    logger.info(
        f"Starting Quiz Platform API - "
        f"Gemini: {settings.has_gemini}, OpenAI: {settings.has_openai}"
    )

    # Validate configuration
    if not settings.has_any_provider:
        logger.warning(
            "No LLM API keys configured. "
            "Set GEMINI_API_KEY and/or OPENAI_API_KEY environment variables."
        )

    yield

    # Shutdown
    logger.info("Shutting down Quiz Platform API")


# Create FastAPI application
app = FastAPI(
    title="Quiz Platform API",
    description="Dynamic MCQ generation via web scraping and LLM",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().log_level.upper() == "DEBUG" else None,
    redoc_url="/redoc" if get_settings().log_level.upper() == "DEBUG" else None,
)

# Configure CORS
settings = get_settings()
origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(quiz.router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to health check."""
    return {"status": "ok", "message": "Quiz Platform API", "docs": "/docs"}


# Lambda handler for AWS deployment
handler = None

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    logger.info("Mangum handler configured for Lambda deployment")
except ImportError:
    logger.debug("Mangum not installed - Lambda deployment unavailable")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
