"""Quiz Platform API - FastAPI Application Entry Point.

Self-hosted deployment optimized for home server with Tailscale Funnel
or Cloudflare Tunnel exposure. Memory footprint < 150MB.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from app.routes import quiz


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler - validates config on startup."""
    try:
        from app.config import get_settings
        settings = get_settings()
        logger.info(
            f"Starting Quiz Platform API - "
            f"Gemini: {settings.has_gemini}, OpenAI: {settings.has_openai}, "
            f"Provider: {settings.llm_provider}"
        )
        if not settings.has_any_provider:
            logger.warning("No LLM API keys configured - quiz generation will fail!")
    except Exception as e:
        logger.error(f"Startup configuration error: {e}")
    yield
    logger.info("Shutting down Quiz Platform API")


# Create FastAPI application
app = FastAPI(
    title="Quiz Platform API",
    description="Dynamic MCQ generation via LLM (Gemini/OpenAI) for self-hosted deployment",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS - will be updated from settings in lifespan if needed
# Default to permissive for development, restrict in production via env
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(quiz.router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Quiz Platform API",
        "version": "2.0.0",
        "description": "Dynamic MCQ generation via LLM",
        "docs": "/docs",
        "health": "/health",
        "generate": "/api/quiz/generate"
    }


@app.get("/health", include_in_schema=False)
async def health_check():
    """Simple health check for load balancers and monitoring."""
    return {"status": "ok", "service": "quiz-platform-api"}


@app.get("/version", include_in_schema=False)
async def version():
    """Version endpoint for deployment verification."""
    return {
        "version": "2.0.0",
        "name": "quiz-platform-api",
        "description": "Self-hosted MCQ quiz platform"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        workers=1,
        loop="uvloop",
        http="httptools"
    )