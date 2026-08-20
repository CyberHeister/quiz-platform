"""FastAPI application entry point with Mangum handler for Lambda."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.routes import quiz
# from app.utils.logger import setup_logging

# setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    try:
        from app.config import get_settings
        settings = get_settings()
        logger.info(
            f"Starting Quiz Platform API - "
            f"Gemini: {settings.has_gemini}, OpenAI: {settings.has_openai}"
        )
        if not settings.has_any_provider:
            logger.warning("No LLM API keys configured.")
    except Exception as e:
        logger.error(f"Startup error: {e}")
    yield
    logger.info("Shutting down Quiz Platform API")


# Create FastAPI application
app = FastAPI(
    title="Quiz Platform API",
    description="Dynamic MCQ generation via web scraping and LLM",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS - use default, will be updated in lifespan if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(quiz.router)

# Force redeploy trigger
@app.get("/version", include_in_schema=False)
async def version():
    """Version endpoint for deployment verification."""
    return {"version": "1.0.2", "deployed_at": "2026-08-20"}


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to health check."""
    return {"status": "ok", "message": "Quiz Platform API", "docs": "/docs"}


@app.get("/health", include_in_schema=False)
async def health_check_simple():
    """Simple health check for Railway/load balancer."""
    return {"status": "ok", "service": "quiz-platform-api"}


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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
