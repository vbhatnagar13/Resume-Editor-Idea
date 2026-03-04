"""Tests for app/services/editor.py — uses mocked LLM."""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from app.models.ir import BulletItem, ResumeEntry, ResumeIR, ResumeSection, TextRun
from app.models.schemas import TailorRequest
from app.services.editor import ResumeEditor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_llm_service(ir: ResumeIR) -> MagicMock:
    """Return an LLMService mock that echoes the input section unchanged."""
    mock = MagicMock()
    mock.tailor_section.side_effect = lambda section, jd, settings: section
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestConservativeNoReorder:
    def test_conservative_no_reorder(self, sample_ir, sample_jd_analysis):
        """With no_reordering=True, section order must remain unchanged."""
        original_section_ids = [s.id for s in sample_ir.sections]

        mock_llm = _mock_llm_service(sample_ir)
        editor = ResumeEditor(llm_service=mock_llm)

        settings = TailorRequest(
            session_id="test",
            job_description="Backend engineer role",
            aggressiveness="conservative",
            no_reordering=True,
        )

        revised_ir = editor.edit(sample_ir, sample_jd_analysis, settings)

        revised_section_ids = [s.id for s in revised_ir.sections]
        assert original_section_ids == revised_section_ids

    def test_balanced_no_reorder_flag(self, sample_ir, sample_jd_analysis):
        """Even in balanced mode, no_reordering=True prevents reordering."""
        original_ids = [s.id for s in sample_ir.sections]

        mock_llm = _mock_llm_service(sample_ir)
        editor = ResumeEditor(llm_service=mock_llm)

        settings = TailorRequest(
            session_id="test",
            job_description="Backend engineer role",
            aggressiveness="balanced",
            no_reordering=True,
        )

        revised_ir = editor.edit(sample_ir, sample_jd_analysis, settings)
        assert [s.id for s in revised_ir.sections] == original_ids


class TestKeywordDensityLimit:
    def test_keyword_density_limit(self, sample_ir, sample_jd_analysis):
        """No bullet should receive more than 3 new keywords from the JD."""
        # Build a mock LLM that stuffs many keywords into each bullet
        jd_keywords = sample_jd_analysis["keywords"]

        def tailor_section_stuffed(section, jd, settings):
            """Return section with bullets overstuffed with keywords."""
            import copy as cp
            revised = cp.deepcopy(section)
            for entry in revised.entries:
                for bullet in entry.bullets:
                    # Append all JD keywords to the bullet (artificial keyword stuffing)
                    bullet.text = bullet.text + " " + " ".join(jd_keywords[:10])
                    bullet.runs = [TextRun(text=bullet.text)]
            return revised

        mock_llm = MagicMock()
        mock_llm.tailor_section.side_effect = tailor_section_stuffed

        editor = ResumeEditor(llm_service=mock_llm)
        settings = TailorRequest(
            session_id="test",
            job_description="Backend engineer role",
            aggressiveness="balanced",
        )

        revised_ir = editor.edit(sample_ir, sample_jd_analysis, settings)

        # Verify keyword density enforcement: each bullet should not have
        # more than 3 new keywords compared to original
        all_kw = set(k.lower() for k in jd_keywords)
        for section in revised_ir.sections:
            orig_section = next(
                (s for s in sample_ir.sections if s.id == section.id), None
            )
            if not orig_section:
                continue
            orig_bullets = {
                b.id: b
                for e in orig_section.entries for b in e.bullets
            }
            for entry in section.entries:
                for bullet in entry.bullets:
                    orig_b = orig_bullets.get(bullet.id)
                    if not orig_b:
                        continue
                    import re
                    orig_kws = set(re.findall(r"\b[a-zA-Z0-9#+.\-]{2,}\b", orig_b.text.lower())) & all_kw
                    rev_kws = set(re.findall(r"\b[a-zA-Z0-9#+.\-]{2,}\b", bullet.text.lower())) & all_kw
                    new_kws = rev_kws - orig_kws
                    assert len(new_kws) <= 3, (
                        f"Bullet '{bullet.id}' has {len(new_kws)} new keywords: {new_kws}"
                    )


class TestNeverChangesEmployerTitle:
    def test_never_changes_employer_title(self, sample_ir, sample_jd_analysis):
        """Editor must never change employer, title, dates after editing."""
        def tailor_section_mutate(section, jd, settings):
            """Deliberately try to mutate employer/title/dates."""
            import copy as cp
            revised = cp.deepcopy(section)
            for entry in revised.entries:
                entry.employer = "HACKED EMPLOYER"
                entry.title = "HACKED TITLE"
                entry.start_date = "Jan 1900"
                entry.end_date = "Dec 1900"
            return revised

        mock_llm = MagicMock()
        mock_llm.tailor_section.side_effect = tailor_section_mutate

        editor = ResumeEditor(llm_service=mock_llm)
        settings = TailorRequest(
            session_id="test",
            job_description="Backend engineer role",
            aggressiveness="aggressive",
        )

        revised_ir = editor.edit(sample_ir, sample_jd_analysis, settings)

        # Original values should be restored
        for orig_section, rev_section in zip(sample_ir.sections, revised_ir.sections):
            for orig_entry, rev_entry in zip(
                orig_section.entries, rev_section.entries
            ):
                assert rev_entry.employer == orig_entry.employer
                assert rev_entry.title == orig_entry.title
                assert rev_entry.start_date == orig_entry.start_date
                assert rev_entry.end_date == orig_entry.end_date
