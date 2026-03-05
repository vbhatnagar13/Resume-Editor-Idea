from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, field_validator

_VALID_AGGRESSIVENESS = {"conservative", "balanced", "aggressive"}


class TailorRequest(BaseModel):
    session_id: str
    job_description: str
    aggressiveness: str = "balanced"  # conservative, balanced, aggressive
    keyword_emphasis: bool = True
    no_reordering: bool = False

    @field_validator("aggressiveness")
    @classmethod
    def validate_aggressiveness(cls, v: str) -> str:
        if v not in _VALID_AGGRESSIVENESS:
            raise ValueError(
                f"aggressiveness must be one of: {', '.join(sorted(_VALID_AGGRESSIVENESS))}"
            )
        return v


class DiffChange(BaseModel):
    section: str
    entry_id: Optional[str] = None
    bullet_id: Optional[str] = None
    change_type: str  # "rewrite", "reorder", "keyword_add"
    original: str
    revised: str
    reason: str


class DiffReport(BaseModel):
    changes: List[DiffChange]
    keywords_added: List[str]
    keywords_preserved: List[str]
    sections_reordered: List[str]
    fabrication_check: str  # "passed" or warning message
    ats_check: str


class TailorResponse(BaseModel):
    session_id: str
    diff_report: DiffReport
    preview_html: str  # simple HTML preview of revised resume
    keyword_score_before: float = 0.0  # 0.0–1.0 fraction of JD keywords in original
    keyword_score_after: float = 0.0   # 0.0–1.0 fraction of JD keywords in revised


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    message: str
