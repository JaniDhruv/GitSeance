"""
🔮 GitSeance — FastAPI Application Entry Point

An Open-Source AI Necromancer that brings dead GitHub repositories
back to life and predicts which files are about to die next.
"""

import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from config import get_settings
from routers import seance, tts
from models.schemas import HealthResponse


# ──────────────────────────────────────────────
# Sentry AI Agent Tracing Setup
# ──────────────────────────────────────────────
settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        send_default_pii=False,
        environment=settings.app_env,
        _experiments={
            "enable_ai_monitoring": True,
        },
    )


# ──────────────────────────────────────────────
# Application Lifespan
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    print("[GitSeance] The necromancer awakens... the spirits stir.")
    yield
    print("[GitSeance] The necromancer rests... the spirits sleep.")


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────
app = FastAPI(
    title="GitSeance",
    description="An Open-Source AI Necromancer that brings dead GitHub repositories back to life.",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS — allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────
app.include_router(seance.router)
app.include_router(tts.router)


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="the spirits are listening",
        version=settings.app_version,
    )


# ──────────────────────────────────────────────
# Static Files (Frontend)
# ──────────────────────────────────────────────
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

