"""
Erebus Backend — FastAPI Application Entry Point
LLM_PROVIDER: groq (llama-3.3-70b-versatile)
"""

# Load .env before ANY module imports so AWS / DB / Redis credentials are set
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=True)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise PostgreSQL tables on startup."""
    try:
        from core.database import init_db
        init_db()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("DB init failed: %s", exc)
    yield

from modules.ranking.router      import router as ranking_router
from modules.analysis.router     import router as analysis_router
from modules.uploads.router      import router as uploads_router
from modules.chat.router         import router as chat_router
from modules.comparison.router import router as comparison_router
from modules.ingestion.router  import router as companies_router
from modules.analytics.router  import router as analytics_router
from modules.auth.router       import router as auth_router, ensure_users_table

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run setup tasks before the app starts accepting requests."""
    try:
        ensure_users_table()
        logger.info("Auth: users table ready")
    except Exception as exc:
        logger.warning(f"Auth table init skipped: {exc}")
    yield  # app runs here

from modules.audio.router      import router as audio_router
from modules.news.router       import router as news_router, dashboard_router as news_dashboard_router
from modules.ocr.router        import router as ocr_router

app = FastAPI(
    title="Erebus API",
    description="Alpha-driven company ranking and signal engine.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)       # POST /auth/register  POST /auth/login
app.include_router(ranking_router)
app.include_router(analysis_router)
app.include_router(uploads_router)
app.include_router(chat_router)
app.include_router(comparison_router)
app.include_router(companies_router)
app.include_router(analytics_router)
app.include_router(audio_router)
app.include_router(news_router)
app.include_router(news_dashboard_router)
app.include_router(ocr_router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Erebus API is running"}


@app.get("/", tags=["Health"])
def root():
    return {"message": "Erebus API is running"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Erebus API"}
