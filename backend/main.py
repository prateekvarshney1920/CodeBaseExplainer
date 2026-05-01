"""
CodeBase Explainer — FastAPI Backend
Main application entry point.
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Create FastAPI app ─────────────────────────────────────────────────────────

app = FastAPI(
    title="CodeBase Explainer API",
    description="AI-powered codebase analysis and explanation tool",
    version="1.0.0",
)

# ── CORS middleware ────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──────────────────────────────────────────────────────────────

from routes.github_route import router as github_router
from routes.upload_route import router as upload_router
from routes.explain_route import router as explain_router

app.include_router(github_router, tags=["GitHub"])
app.include_router(upload_router, tags=["Upload"])
app.include_router(explain_router, tags=["Explain"])


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    port = os.getenv("PORT", "8000")
    groq_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    github_token = os.getenv("GITHUB_TOKEN", "")

    logger.info("=" * 60)
    logger.info("  CodeBase Explainer API — Starting")
    logger.info("=" * 60)
    logger.info(f"  Port: {port}")
    logger.info(f"  Groq API Key:   {'✓ configured' if groq_key and groq_key != 'your_groq_api_key_here' else '✗ not set'}")
    logger.info(f"  Groq Model:     {groq_model}")
    logger.info(f"  GitHub Token:   {'✓ configured' if github_token and github_token != 'your_github_token_here_optional' else '✗ not set (public repos only)'}")
    logger.info("=" * 60)
