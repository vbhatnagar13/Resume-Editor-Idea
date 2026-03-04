"""Shared test fixtures for the resume tailor backend tests."""

from __future__ import annotations

import sys
import os
import uuid
from typing import Any, Dict
import pytest

# Make 'app' importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.ir import BulletItem, ResumeEntry, ResumeIR, ResumeSection, TextRun


def _bullet(text: str, bold: bool = False) -> BulletItem:
    bid = str(uuid.uuid4())
    return BulletItem(
        id=bid,
        text=text,
        runs=[TextRun(text=text, bold=bold)],
        level=0,
        original_text=text,
    )


def _entry(employer: str, title: str, bullets) -> ResumeEntry:
    return ResumeEntry(
        id=str(uuid.uuid4()),
        employer=employer,
        title=title,
        start_date="Jan 2020",
        end_date="Present",
        location="New York, NY",
        bullets=bullets,
    )


@pytest.fixture
def sample_ir() -> ResumeIR:
    """A minimal ResumeIR with one experience section and one skills section."""
    exp_entry = _entry(
        employer="Acme Corp",
        title="Software Engineer",
        bullets=[
            _bullet("Developed REST APIs using Python and Django"),
            _bullet("Collaborated with cross-functional teams to deliver features"),
        ],
    )
    exp_section = ResumeSection(
        id=str(uuid.uuid4()),
        heading="Experience",
        heading_style={"bold": True, "font_size": 12.0},
        section_type="experience",
        entries=[exp_entry],
    )

    skills_item = _bullet("Python, Django, REST APIs, SQL, Docker")
    skills_section = ResumeSection(
        id=str(uuid.uuid4()),
        heading="Skills",
        heading_style={"bold": True, "font_size": 12.0},
        section_type="skills",
        plain_items=[skills_item],
    )

    return ResumeIR(
        source_format="docx",
        sections=[exp_section, skills_section],
        contact_info={"name": "Jane Doe", "email": "jane@example.com"},
        has_tables=False,
    )


@pytest.fixture
def sample_jd_analysis() -> Dict[str, Any]:
    """A sample JD analysis dict."""
    return {
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "preferred_skills": ["Kubernetes", "AWS", "GraphQL"],
        "responsibilities": [
            "Design and implement scalable microservices",
            "Write clean, maintainable code",
            "Collaborate with product and design teams",
        ],
        "keywords": ["microservices", "FastAPI", "PostgreSQL", "scalable", "Docker", "CI/CD"],
        "seniority": "mid",
        "job_title": "Backend Software Engineer",
        "industry": "Technology",
        "key_technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
        "soft_skills": ["communication", "collaboration", "problem-solving"],
    }
