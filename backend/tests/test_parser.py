"""Tests for app/services/parser.py"""

from __future__ import annotations

import io
import uuid

import pytest

from app.models.ir import ResumeIR


# ---------------------------------------------------------------------------
# Helpers to build in-memory DOCX
# ---------------------------------------------------------------------------

def _make_minimal_docx() -> bytes:
    """Create a minimal DOCX with heading + bullets using python-docx."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()

    # Contact
    p = doc.add_paragraph("Jane Doe")
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(16)

    doc.add_paragraph("jane@example.com | 555-123-4567")

    # Section heading
    p = doc.add_paragraph("EXPERIENCE")
    for run in p.runs:
        run.bold = True
        run.font.size = Pt(12)

    # Entry header
    p = doc.add_paragraph("Acme Corp | Software Engineer  Jan 2020 – Present")
    run = p.runs[0]
    run.bold = True

    # Bullets
    doc.add_paragraph("• Developed REST APIs using Python and Django", style="List Bullet")
    doc.add_paragraph("• Collaborated with cross-functional teams", style="List Bullet")

    # Skills heading
    p = doc.add_paragraph("SKILLS")
    for run in p.runs:
        run.bold = True
        run.font.size = Pt(12)

    doc.add_paragraph("• Python, Django, REST APIs, SQL")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _make_bold_heading_docx() -> bytes:
    """DOCX where headings are identified by bold + larger font."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()

    # Regular paragraph (base size ~11pt)
    p = doc.add_paragraph("Some regular content")
    p.runs[0].font.size = Pt(11)

    # Heading: bold + 14pt
    p = doc.add_paragraph("EDUCATION")
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(14)

    # Sub-content
    doc.add_paragraph("• Bachelor of Science in Computer Science")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _make_formatted_bullets_docx() -> bytes:
    """DOCX with bullets that have mixed bold/italic runs."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()

    p = doc.add_paragraph("EXPERIENCE")
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(12)

    p = doc.add_paragraph("TechCorp | Lead Engineer  2019 – 2022")
    p.runs[0].bold = True

    # Bullet with mixed formatting
    p = doc.add_paragraph(style="List Bullet")
    r1 = p.add_run("Led ")
    r1.bold = False
    r2 = p.add_run("team of 5")
    r2.bold = True
    r3 = p.add_run(" engineers to deliver project on time")
    r3.bold = False

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseDocxBasic:
    def test_parse_docx_basic(self):
        """Parse a minimal DOCX and verify sections are detected."""
        from app.services.parser import parse_docx

        file_bytes = _make_minimal_docx()
        ir = parse_docx(file_bytes)

        assert isinstance(ir, ResumeIR)
        assert ir.source_format == "docx"
        assert len(ir.sections) >= 1

    def test_section_types_detected(self):
        """Experience and skills sections should be classified correctly."""
        from app.services.parser import parse_docx

        file_bytes = _make_minimal_docx()
        ir = parse_docx(file_bytes)

        section_types = {s.section_type for s in ir.sections}
        # At least one section should be experience or skills
        assert section_types & {"experience", "skills"}


class TestDetectSectionHeadings:
    def test_detect_section_headings(self):
        """Bold + larger font text should be detected as a section heading."""
        from app.services.parser import parse_docx

        file_bytes = _make_bold_heading_docx()
        ir = parse_docx(file_bytes)

        headings = [s.heading for s in ir.sections]
        assert any("EDUCATION" in h for h in headings)

    def test_education_section_type(self):
        """EDUCATION heading should yield section_type='education'."""
        from app.services.parser import parse_docx

        file_bytes = _make_bold_heading_docx()
        ir = parse_docx(file_bytes)

        education_sections = [s for s in ir.sections if s.section_type == "education"]
        assert len(education_sections) >= 1


class TestPreserveBulletFormatting:
    def test_preserve_bullet_formatting(self):
        """Bullet runs with bold/italic should be preserved in the IR."""
        from app.services.parser import parse_docx

        file_bytes = _make_formatted_bullets_docx()
        ir = parse_docx(file_bytes)

        # Find bullets across all sections
        all_bullets = [
            b
            for s in ir.sections
            for e in s.entries
            for b in e.bullets
        ]

        # At least one bullet should have multiple runs (mixed formatting)
        multi_run_bullets = [b for b in all_bullets if len(b.runs) > 1]
        assert len(multi_run_bullets) >= 1

    def test_bold_run_preserved(self):
        """A bold run in a bullet should have run.bold == True."""
        from app.services.parser import parse_docx

        file_bytes = _make_formatted_bullets_docx()
        ir = parse_docx(file_bytes)

        all_runs = [
            r
            for s in ir.sections
            for e in s.entries
            for b in e.bullets
            for r in b.runs
        ]
        bold_runs = [r for r in all_runs if r.bold]
        assert len(bold_runs) >= 1
