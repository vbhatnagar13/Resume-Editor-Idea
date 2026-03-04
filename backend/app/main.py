"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import download, tailor, upload

app = FastAPI(
    title="Resume Tailor API",
    version="1.0.0",
    description="Tailor resumes to job descriptions using AI",
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
