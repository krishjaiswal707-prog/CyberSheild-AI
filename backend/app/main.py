"""
FastAPI application entry point.

Registers all routers under /api/v1, configures CORS for the React frontend,
sets up logging, and exposes a health check endpoint.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    analysis,
    analytics,
    checklist,
    community,
    complaint,
    deepfake,
    history,
    hotline,
    scammer_db,
    whatsapp,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Digital Arrest Scam Detector API starting up...")
    logger.info("   Claude model: %s", settings.claude_model)
    logger.info("   Environment: %s", settings.app_env)

    # Auto-create tables & seed database for seamless out-of-the-box execution
    try:
        from app.database import engine, Base, AsyncSessionLocal
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("   Database tables checked/created.")

        # Seed data idempotently
        async with AsyncSessionLocal() as session:
            from seed_data import seed_known_scammers, seed_community_reports, seed_demo_analyses, seed_demo_session
            await seed_known_scammers(session)
            await seed_community_reports(session)
            await seed_demo_analyses(session)
            await seed_demo_session(session)
        logger.info("   Database seeded with initial demo data.")
    except Exception as exc:
        logger.warning("   Database auto-initialisation warning: %s", exc)

    yield
    logger.info("API shutting down.")



# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CyberSheild-AI — Digital Arrest Scam Detector API",
    description=(
        "WhatsApp-based AI scam detection backend for Indian digital safety. "
        "Detects digital arrest scams via rule engine + Claude AI. "
        "Built for the Indian Digital Public Safety Hackathon."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(analysis.router,    prefix=API_PREFIX)
app.include_router(complaint.router,   prefix=API_PREFIX)
app.include_router(scammer_db.router,  prefix=API_PREFIX)
app.include_router(history.router,     prefix=API_PREFIX)
app.include_router(deepfake.router,    prefix=API_PREFIX)
app.include_router(community.router,   prefix=API_PREFIX)
app.include_router(hotline.router,     prefix=API_PREFIX)
app.include_router(checklist.router,   prefix=API_PREFIX)
app.include_router(analytics.router,   prefix=API_PREFIX)
app.include_router(whatsapp.router,    prefix=API_PREFIX)


import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check for production built React frontend in frontend/dist first
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
APP_STATIC = Path(__file__).parent / "static"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
elif APP_STATIC.exists():
    app.mount("/static", StaticFiles(directory=APP_STATIC), name="static")


# ── Health Check & UI ──────────────────────────────────────────────────────────
@app.get("/", tags=["UI & Health"])
async def root():
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    elif APP_STATIC.exists() and (APP_STATIC / "index.html").exists():
        return FileResponse(APP_STATIC / "index.html")
    return {
        "service": "CyberSheild-AI — Digital Arrest Scam Detector API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }



@app.get("/health", tags=["UI & Health"])
async def health() -> dict:
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claude_model": settings.claude_model,
        "environment": settings.app_env,
    }

