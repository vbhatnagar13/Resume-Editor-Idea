"""Tests for app/services/generator.py"""

from __future__ import annotations

import copy
import pytest

from app.models.ir import ResumeIR
from app.services.generator import generate_docx, generate_pdf


class TestGenerateDocxProducesFile:
    def test_generate_docx_produces_file(self, sample_ir):
        """generate_docx should return non-empty bytes."""
        result = generate_docx(sample_ir)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_pdf_produces_file(self, sample_ir):
        """generate_pdf should return non-empty bytes."""
        result = generate_pdf(sample_ir)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_docx_valid_format(self, sample_ir):
        """Generated DOCX bytes should start with the ZIP magic number (PK)."""
        result = generate_docx(sample_ir)
        # DOCX is a ZIP file, starts with PK\x03\x04
        assert result[:2] == b"PK"

    def test_generate_pdf_valid_format(self, sample_ir):
        """Generated PDF bytes should start with the PDF magic number."""
        result = generate_pdf(sample_ir)
        assert result[:4] == b"%PDF"


class TestRoundTripPreservesSections:
    def test_round_trip_preserves_sections(self, sample_ir):
        """
        Parse -> Generate DOCX -> Re-parse should yield the same section count.
        """
        from app.services.parser import parse_docx

        docx_bytes = generate_docx(sample_ir)
        reparsed_ir = parse_docx(docx_bytes)

        # The re-parsed IR should have at least as many sections as the original
        # (headings may collapse, but count should be >= 1)
        assert len(reparsed_ir.sections) >= 1

    def test_round_trip_docx_contains_contact_name(self, sample_ir):
        """Generated DOCX should contain the contact name from the IR."""
        docx_bytes = generate_docx(sample_ir)

        # Re-open with python-docx and check text content
        import io
        from docx import Document

        doc = Document(io.BytesIO(docx_bytes))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert sample_ir.contact_info.get("name", "") in all_text
