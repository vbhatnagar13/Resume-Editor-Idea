"""POST /api/tailor — Run the full tailoring pipeline."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.ir import ResumeIR
from app.models.schemas import TailorRequest, TailorResponse
from app.services.diff import generate_diff
from app.services.editor import ResumeEditor
from app.services.generator import generate_docx, generate_pdf
from app.services.llm import LLMService, OpenAIClient, create_llm_service
from app.services.parser import parse_resume

router = APIRouter()

SESSION_DIR = Path(os.environ.get("SESSION_DIR", "/tmp/sessions"))


def _get_session_path(session_id: str) -> Path:
    path = SESSION_DIR / session_id
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return path


def _load_resume_file(session_path: Path) -> tuple[bytes, str]:
    for ext in ("docx", "pdf"):
        candidate = session_path / f"resume.{ext}"
        if candidate.exists():
            return candidate.read_bytes(), f"resume.{ext}"
    raise HTTPException(status_code=404, detail="Resume file not found in session.")


def _build_preview_html(ir: ResumeIR) -> str:
    """Generate a simple HTML preview of the resume."""
    lines = ["<div class='resume-preview'>"]
    contact = ir.contact_info
    if contact.get("name"):
        lines.append(f"<h1 class='text-2xl font-bold text-center'>{contact['name']}</h1>")
    contact_parts = [v for k, v in contact.items() if k != "name" and v]
    if contact_parts:
        lines.append(
            f"<p class='text-center text-sm'>{' | '.join(contact_parts)}</p>"
        )

    for section in ir.sections:
        lines.append(f"<h2 class='section-heading'>{section.heading}</h2>")
        lines.append("<hr />")

        if section.section_type in ("skills", "summary"):
            lines.append("<ul>")
            for item in section.plain_items:
                lines.append(f"<li>{_escape(item.text)}</li>")
            lines.append("</ul>")
        else:
            for entry in section.entries:
                header_parts = []
                if entry.employer:
                    header_parts.append(f"<strong>{_escape(entry.employer)}</strong>")
                if entry.title:
                    header_parts.append(_escape(entry.title))
                date_parts = []
                if entry.start_date:
                    date_parts.append(entry.start_date)
                if entry.end_date:
                    date_parts.append(entry.end_date)
                if header_parts or date_parts:
                    header = " | ".join(header_parts)
                    if date_parts:
                        header += f" <em>{' – '.join(date_parts)}</em>"
                    lines.append(f"<p>{header}</p>")
                if entry.bullets:
                    lines.append("<ul>")
                    for b in entry.bullets:
                        lines.append(f"<li>{_escape(b.text)}</li>")
                    lines.append("</ul>")

    lines.append("</div>")
    return "\n".join(lines)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@router.post("/tailor", response_model=TailorResponse)
async def tailor_resume(request: TailorRequest) -> TailorResponse:
    """
    Run the full tailoring pipeline:
    1. Load resume from session
    2. Parse into IR
    3. Analyze JD with LLM
    4. Edit IR with LLM
    5. Verify for fabrication
    6. Generate diff report
    7. Save output files
    8. Return TailorResponse
    """
    session_path = _get_session_path(request.session_id)

    file_bytes, filename = _load_resume_file(session_path)

    # Build LLM service (fails gracefully if key not set)
    try:
        llm_service = create_llm_service()
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Parse resume
    try:
        original_ir = parse_resume(file_bytes, filename)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {exc}")

    # Analyze JD
    jd_analysis = llm_service.analyze_job_description(request.job_description)

    # Edit resume
    editor = ResumeEditor(llm_service=llm_service)
    revised_ir = editor.edit(original_ir, jd_analysis, request)

    # Verify
    verification = llm_service.verify_resume(original_ir, revised_ir, jd_analysis)
    fabrication_msg = (
        "passed"
        if not verification.get("fabrication_detected")
        else ("WARNING: " + "; ".join(verification.get("fabrication_details", [])))
    )
    ats_msg = verification.get("ats_check", "ATS-friendly")

    # Generate diff
    diff_report = generate_diff(original_ir, revised_ir)
    diff_report.fabrication_check = fabrication_msg
    diff_report.ats_check = ats_msg

    # Save output files
    docx_bytes = generate_docx(revised_ir)
    pdf_bytes = generate_pdf(revised_ir)
    (session_path / "output.docx").write_bytes(docx_bytes)
    (session_path / "output.pdf").write_bytes(pdf_bytes)

    # Save revised IR for later reference
    (session_path / "revised_ir.json").write_text(
        revised_ir.model_dump_json(indent=2), encoding="utf-8"
    )

    preview_html = _build_preview_html(revised_ir)

    return TailorResponse(
        session_id=request.session_id,
        diff_report=diff_report,
        preview_html=preview_html,
    )
