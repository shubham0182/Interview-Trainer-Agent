"""
InterviewPro AI — FastAPI application entry point.

Registers all API v1 routers, configures CORS, and sets up
the application lifecycle (startup/shutdown events).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import auth, profiles

app = FastAPI(
    title="InterviewPro AI",
    description="AI-powered interview preparation platform — AICTE 2026 PS22",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])

# Registered in later sub-tasks:
# from app.api.v1 import sessions, answers, reports
# app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
# app.include_router(answers.router, prefix="/api/v1/answers", tags=["answers"])
# app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Liveness probe — returns 200 when the server is up."""
    return {"status": "ok", "service": "InterviewPro AI Backend"}
