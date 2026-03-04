"""POST /api/upload — Accept a resume file and job description."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import UploadResponse

router = APIRouter()

SESSION_DIR = Path(os.environ.get("SESSION_DIR", "/tmp/sessions"))
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
) -> UploadResponse:
    """
    Accept a resume (PDF or DOCX) and a job description text.
    Store both in a session directory and return the session_id.
    """
    filename = file.filename or "resume"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MB limit.",
        )

    session_id = str(uuid.uuid4())
    session_path = SESSION_DIR / session_id
    session_path.mkdir(parents=True, exist_ok=True)

    (session_path / f"resume.{ext}").write_bytes(file_bytes)
    (session_path / "job_description.txt").write_text(job_description, encoding="utf-8")
    (session_path / "original_filename.txt").write_text(filename, encoding="utf-8")

    return UploadResponse(
        session_id=session_id,
        filename=filename,
        message="Resume uploaded successfully.",
    )
