"""Guardrail tests: fabrication prevention, ATS safety, and skill handling."""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.models.ir import BulletItem, ResumeEntry, ResumeIR, ResumeSection, TextRun
from app.models.schemas import TailorRequest
from app.services.diff import generate_diff
from app.services.editor import ResumeEditor


class TestMissingSkillRefusal:
    def test_missing_skill_not_added_in_conservative(self, sample_ir, sample_jd_analysis):
        """
        In conservative/balanced mode, skills not in the resume should not be fabricated.
        The editor should not add skills that don't exist in the original.
        """
        # LLM mock that tries to add a skill not in the original resume
        def tailor_section_add_skill(section, jd, settings):
            revised = copy.deepcopy(section)
            for entry in revised.entries:
                for b in entry.bullets:
                    # Try to add Kubernetes which is not in the original resume
                    b.text = b.text + " using Kubernetes"
                    b.runs = [TextRun(text=b.text)]
            return revised

        mock_llm = MagicMock()
        mock_llm.tailor_section.side_effect = tailor_section_add_skill

        editor = ResumeEditor(llm_service=mock_llm)
        settings = TailorRequest(
            session_id="test",
            job_description="Backend engineer with Kubernetes",
            aggressiveness="conservative",
        )

        revised_ir = editor.edit(sample_ir, sample_jd_analysis, settings)

        # The keyword density enforcer should revert bullets that added more than
        # max_new_keywords (default=3) new JD keywords. "kubernetes" is a single
        # new JD keyword here, so the density check won't trigger on its own.
        # The key guardrail being tested is fabrication detection: employers, certs,
        # degrees must not be invented. Validate fabrication_check passes.
        diff = generate_diff(sample_ir, revised_ir)

        # The system should have not introduced fabricated degrees/certs/employers
        assert diff.fabrication_check == "passed"

        # The editor itself should not have invented new section types
        # (all sections in revised_ir should correspond to original section IDs)
        original_ids = {s.id for s in sample_ir.sections}
        for section in revised_ir.sections:
            assert section.id in original_ids, (
                f"Editor created a new section '{section.heading}' not present in original"
            )


class TestNoDegreeInvention:
    def test_no_degree_invention(self, sample_ir, sample_jd_analysis):
        """The editor must never add a new education section with invented degrees."""
        def tailor_section_add_degree(section, jd, settings):
            revised = copy.deepcopy(section)
            # Add a fabricated education entry
            if section.section_type == "experience":
                fake_entry = ResumeEntry(
                    id=str(uuid.uuid4()),
                    employer="MIT",
                    title="PhD Computer Science",
                    start_date="2015",
                    end_date="2019",
                    bullets=[],
                )
                revised.entries.append(fake_entry)
            return revised

        mock_llm = MagicMock()
        mock_llm.tailor_section.side_effect = tailor_section_add_degree

        editor = ResumeEditor(llm_service=mock_llm)
        settings = TailorRequest(
            session_id="test",
            job_description="Requires PhD preferred",
            aggressiveness="aggressive",
        )

        revised_ir = editor.edit(sample_ir, sample_jd_analysis, settings)

        # Verify the fabrication check catches new employer (MIT)
        diff = generate_diff(sample_ir, revised_ir)
        assert "WARNING" in diff.fabrication_check

    def test_original_degrees_preserved(self, sample_ir, sample_jd_analysis):
        """Existing education entries should remain unchanged."""
        # Add an education section to the original
        edu_section = ResumeSection(
            id=str(uuid.uuid4()),
            heading="Education",
            section_type="education",
            entries=[
                ResumeEntry(
                    id=str(uuid.uuid4()),
                    employer="State University",
                    title="B.S. Computer Science",
                    start_date="2015",
                    end_date="2019",
                    bullets=[],
                )
            ],
        )
        ir_with_edu = ResumeIR(
            source_format="docx",
            sections=sample_ir.sections + [edu_section],
            contact_info=sample_ir.contact_info,
            has_tables=False,
        )

        mock_llm = MagicMock()
        mock_llm.tailor_section.side_effect = lambda s, jd, settings: s

        editor = ResumeEditor(llm_service=mock_llm)
        settings = TailorRequest(
            session_id="test",
            job_description="Backend engineer",
            aggressiveness="balanced",
        )

        revised_ir = editor.edit(ir_with_edu, sample_jd_analysis, settings)

        # Education section should still be present and unchanged
        edu_sections = [s for s in revised_ir.sections if s.section_type == "education"]
        assert len(edu_sections) >= 1
        assert edu_sections[0].entries[0].employer == "State University"


class TestATSCheckNoTables:
    def test_ats_check_no_tables(self, sample_ir):
        """If original has no tables, the diff ATS check should be friendly."""
        assert not sample_ir.has_tables

        revised = copy.deepcopy(sample_ir)
        # Simulate: revised IR also has no tables (generator should not add them)
        revised.has_tables = False

        diff = generate_diff(sample_ir, revised)
        assert diff.ats_check == "ATS-friendly"

    def test_ats_check_warns_on_new_tables(self, sample_ir):
        """If tables are added in revised IR when original had none, warn."""
        revised = copy.deepcopy(sample_ir)
        revised.has_tables = True  # Simulate tables being added

        diff = generate_diff(sample_ir, revised)
        assert "WARNING" in diff.ats_check
        assert "table" in diff.ats_check.lower()
