from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TextRun(BaseModel):
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    font_size: Optional[float] = None
    font_name: Optional[str] = None


class BulletItem(BaseModel):
    id: str  # uuid
    text: str  # plain text of bullet
    runs: List[TextRun]  # styled runs
    level: int = 0  # indent level
    original_text: str  # for diff tracking


class ResumeEntry(BaseModel):
    id: str
    employer: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    bullets: List[BulletItem] = []


class ResumeSection(BaseModel):
    id: str
    heading: str
    heading_style: Dict[str, Any] = {}  # bold, font_size, etc.
    section_type: str  # "experience", "education", "skills", "summary", "other"
    entries: List[ResumeEntry] = []
    plain_items: List[BulletItem] = []  # for skills/summary sections


class ResumeIR(BaseModel):
    source_format: str  # "docx" or "pdf"
    sections: List[ResumeSection]
    metadata: Dict[str, Any] = {}
    contact_info: Dict[str, str] = {}
    has_tables: bool = False
