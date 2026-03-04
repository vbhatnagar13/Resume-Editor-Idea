"""Tests for app/services/diff.py"""

from __future__ import annotations

import copy
import uuid

import pytest

from app.models.ir import BulletItem, ResumeEntry, ResumeIR, ResumeSection, TextRun
from app.services.diff import generate_diff


class TestDiffReportCapturesRewrites:
    def test_diff_report_captures_rewrites(self, sample_ir):
        """Modifying a bullet should be captured as a 'rewrite' or 'keyword_add' change."""
        revised = copy.deepcopy(sample_ir)

        # Modify the first bullet in the first entry of the first section
        first_section = revised.sections[0]
        first_entry = first_section.entries[0]
        original_text = first_entry.bullets[0].text
        first_entry.bullets[0].text = (
            "Designed and implemented scalable FastAPI microservices using PostgreSQL"
        )
        first_entry.bullets[0].runs = [
            TextRun(text=first_entry.bullets[0].text)
        ]

        diff = generate_diff(sample_ir, revised)

        assert len(diff.changes) >= 1
        # The change should reference the modified section
        modified_change = next(
            (c for c in diff.changes if c.original == original_text), None
        )
        assert modified_change is not None
        assert modified_change.change_type in ("rewrite", "keyword_add")

    def test_no_changes_when_identical(self, sample_ir):
        """No diff changes if both IRs are identical."""
        diff = generate_diff(sample_ir, sample_ir)
        assert len(diff.changes) == 0


class TestFabricationCheckDetectsNewEmployer:
    def test_fabrication_check_detects_new_employer(self, sample_ir):
        """Adding a new employer in the revised IR should trigger fabrication warning."""
        revised = copy.deepcopy(sample_ir)

        # Add a completely new entry with a new employer
        new_entry = ResumeEntry(
            id=str(uuid.uuid4()),
            employer="FakeCompany LLC",
            title="Senior Engineer",
            start_date="Jan 2023",
            end_date="Present",
            bullets=[
                BulletItem(
                    id=str(uuid.uuid4()),
                    text="Invented a new technology",
                    runs=[TextRun(text="Invented a new technology")],
                    level=0,
                    original_text="Invented a new technology",
                )
            ],
        )
        revised.sections[0].entries.append(new_entry)

        diff = generate_diff(sample_ir, revised)

        assert "WARNING" in diff.fabrication_check
        assert "FakeCompany LLC" in diff.fabrication_check or "employer" in diff.fabrication_check.lower()

    def test_fabrication_check_passes_with_same_employers(self, sample_ir):
        """If employers are unchanged, fabrication check should pass."""
        revised = copy.deepcopy(sample_ir)
        # Only modify bullet text, not employer
        revised.sections[0].entries[0].bullets[0].text = "Different text"

        diff = generate_diff(sample_ir, revised)
        assert diff.fabrication_check == "passed"
