"""FastAPI application entry point."""

from __future__ import annotations

import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import download, tailor, upload

SESSION_DIR = Path(os.environ.get("SESSION_DIR", "/tmp/sessions"))
SESSION_MAX_AGE_SECONDS = 3600  # 1 hour


def _cleanup_old_sessions() -> int:
    """Delete session directories older than SESSION_MAX_AGE_SECONDS. Returns count deleted."""
    if not SESSION_DIR.exists():
        return 0
    cutoff = time.time() - SESSION_MAX_AGE_SECONDS
    deleted = 0
    for session_path in SESSION_DIR.iterdir():
        if session_path.is_dir():
            try:
                if session_path.stat().st_mtime < cutoff:
                    shutil.rmtree(session_path, ignore_errors=True)
                    deleted += 1
            except OSError:
                pass
    return deleted


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Clean up stale sessions on startup."""
    _cleanup_old_sessions()
    yield


app = FastAPI(
    title="Resume Tailor API",
    version="1.0.0",
    description="Tailor resumes to job descriptions using AI",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(tailor.router, prefix="/api", tags=["tailor"])
app.include_router(download.router, prefix="/api", tags=["download"])


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
