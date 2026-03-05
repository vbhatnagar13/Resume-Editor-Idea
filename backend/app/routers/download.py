"""GET /api/download/{session_id}/{format} — Serve generated resume files."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

SESSION_DIR = Path(os.environ.get("SESSION_DIR", "/tmp/sessions"))

MIME_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


@router.get("/download/{session_id}/{fmt}")
async def download_file(session_id: str, fmt: str) -> FileResponse:
    """Download the tailored resume in DOCX or PDF format."""
    if fmt not in ("docx", "pdf"):
        raise HTTPException(
            status_code=400,
            detail="Format must be 'docx' or 'pdf'.",
        )

    session_path = SESSION_DIR / session_id
    if not session_path.exists():
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    output_file = session_path / f"output.{fmt}"
    if not output_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Output file not found. Run /api/tailor first.",
        )

    original_filename_file = session_path / "original_filename.txt"
    original_name = "resume"
    if original_filename_file.exists():
        original_name = original_filename_file.read_text(encoding="utf-8").strip()
        original_name = original_name.rsplit(".", 1)[0]

    download_name = f"{original_name}_tailored.{fmt}"

    return FileResponse(
        path=str(output_file),
        media_type=MIME_TYPES[fmt],
        filename=download_name,
    )
