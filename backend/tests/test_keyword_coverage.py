"""Tests for keyword coverage scoring and aggressiveness validation."""

from __future__ import annotations

import copy
import uuid

import pytest

from app.models.ir import BulletItem, ResumeEntry, ResumeIR, ResumeSection, TextRun
from app.models.schemas import TailorRequest
from app.services.diff import compute_keyword_coverage


def _make_ir(bullet_texts: list, skill_texts: list | None = None) -> ResumeIR:
    bullets = [
        BulletItem(
            id=str(uuid.uuid4()),
            text=t,
            runs=[TextRun(text=t)],
            level=0,
            original_text=t,
        )
        for t in bullet_texts
    ]
    entry = ResumeEntry(
        id=str(uuid.uuid4()),
        employer="ACME",
        title="Engineer",
        bullets=bullets,
    )
    exp_section = ResumeSection(
        id=str(uuid.uuid4()),
        heading="Experience",
        heading_style={},
        section_type="experience",
        entries=[entry],
    )
    sections = [exp_section]

    if skill_texts:
        skill_items = [
            BulletItem(
                id=str(uuid.uuid4()),
                text=t,
                runs=[TextRun(text=t)],
                level=0,
                original_text=t,
            )
            for t in skill_texts
        ]
        sections.append(
            ResumeSection(
                id=str(uuid.uuid4()),
                heading="Skills",
                heading_style={},
                section_type="skills",
                plain_items=skill_items,
            )
        )

    return ResumeIR(source_format="docx", sections=sections, has_tables=False)


class TestKeywordCoverage:
    def test_full_coverage_returns_one(self):
        """If all JD keywords are in the resume, score should be 1.0."""
        ir = _make_ir(["Python FastAPI Docker microservices PostgreSQL CI/CD scalable"])
        keywords = ["python", "fastapi", "docker", "microservices"]
        score = compute_keyword_coverage(ir, keywords)
        assert score == 1.0

    def test_zero_coverage_returns_zero(self):
        """If no JD keywords are in the resume, score should be 0.0."""
        ir = _make_ir(["Designed user interfaces using HTML and CSS"])
        keywords = ["python", "fastapi", "docker", "kubernetes"]
        score = compute_keyword_coverage(ir, keywords)
        assert score == 0.0

    def test_partial_coverage(self):
        """Partial keyword match returns the right fraction."""
        ir = _make_ir(["Python and Docker are used here"])
        keywords = ["python", "docker", "kubernetes", "fastapi"]
        score = compute_keyword_coverage(ir, keywords)
        # 2 out of 4 keywords covered
        assert score == 0.5

    def test_empty_keywords_returns_one(self):
        """Empty keyword list should return 1.0 (no keywords to miss)."""
        ir = _make_ir(["Any text here"])
        assert compute_keyword_coverage(ir, []) == 1.0

    def test_skills_section_contributes_to_score(self):
        """Keywords in the skills section should count toward coverage."""
        ir = _make_ir(
            bullet_texts=["Designed scalable systems"],
            skill_texts=["Python, FastAPI, Docker"],
        )
        keywords = ["python", "fastapi", "docker"]
        score = compute_keyword_coverage(ir, keywords)
        assert score == 1.0

    def test_score_improves_after_edit(self):
        """Coverage score should be >= before after we add more keywords."""
        ir_before = _make_ir(["Developed APIs using Python"])
        ir_after = _make_ir(["Developed REST APIs using Python, FastAPI, and Docker"])
        keywords = ["python", "fastapi", "docker", "rest"]
        score_before = compute_keyword_coverage(ir_before, keywords)
        score_after = compute_keyword_coverage(ir_after, keywords)
        assert score_after >= score_before


class TestAggressivenessValidation:
    def test_valid_values_accepted(self):
        """conservative, balanced, aggressive should all be valid."""
        for value in ("conservative", "balanced", "aggressive"):
            req = TailorRequest(
                session_id="test",
                job_description="Some JD text",
                aggressiveness=value,
            )
            assert req.aggressiveness == value

    def test_invalid_value_raises(self):
        """Invalid aggressiveness values should raise a ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TailorRequest(
                session_id="test",
                job_description="Some JD text",
                aggressiveness="extreme",
            )

    def test_default_is_balanced(self):
        """Default aggressiveness should be 'balanced'."""
        req = TailorRequest(session_id="test", job_description="Some JD text")
        assert req.aggressiveness == "balanced"
