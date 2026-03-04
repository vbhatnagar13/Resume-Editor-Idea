"""Resume editing algorithm that drives LLM-based tailoring."""

from __future__ import annotations

from typing import Any, Dict, List, Set

from app.models.ir import BulletItem, ResumeEntry, ResumeIR, ResumeSection
from app.models.schemas import TailorRequest
from app.services.llm import LLMService


# ---------------------------------------------------------------------------
# Keyword overlap
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> Set[str]:
    """Return a set of lowercase words from text."""
    import re
    return set(re.findall(r"\b[a-zA-Z0-9#+.\-]{2,}\b", text.lower()))


def _keyword_overlap(text: str, keywords: List[str]) -> float:
    """Return fraction of JD keywords present in text (0.0 – 1.0)."""
    if not keywords:
        return 1.0
    tokens = _tokenize(text)
    kw_tokens = {k.lower() for k in keywords}
    matched = tokens & kw_tokens
    return len(matched) / len(kw_tokens)


# ---------------------------------------------------------------------------
# Relevance scoring for entry reordering
# ---------------------------------------------------------------------------

def _entry_relevance(entry: ResumeEntry, keywords: List[str]) -> float:
    """Score an entry by keyword coverage across all bullets."""
    all_text = " ".join(b.text for b in entry.bullets)
    if entry.title:
        all_text += " " + entry.title
    return _keyword_overlap(all_text, keywords)


# ---------------------------------------------------------------------------
# Editor
# ---------------------------------------------------------------------------

class ResumeEditor:
    """Orchestrates the editing pipeline using the LLM service."""

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service

    def edit(
        self,
        ir: ResumeIR,
        jd_analysis: Dict[str, Any],
        settings: TailorRequest,
    ) -> ResumeIR:
        """
        Main editing algorithm.

        1. Determine which bullets/entries need editing based on aggressiveness.
        2. Delegate to LLM for section rewrites.
        3. Apply post-processing: reorder if allowed, enforce limits.
        4. Preserve immutable fields.
        """
        all_keywords: List[str] = (
            jd_analysis.get("keywords", [])
            + jd_analysis.get("required_skills", [])
            + jd_analysis.get("key_technologies", [])
        )

        edited_sections: List[ResumeSection] = []

        for section in ir.sections:
            if section.section_type not in ("experience", "skills", "summary", "other"):
                edited_sections.append(section)
                continue

            # Determine if any bullets need editing
            if not _section_needs_editing(section, all_keywords, settings.aggressiveness):
                edited_sections.append(section)
                continue

            # Delegate to LLM
            revised_section = self._llm.tailor_section(section, jd_analysis, settings)

            # Post-process: preserve immutable fields
            revised_section = _preserve_immutable_fields(section, revised_section)

            # Post-process: enforce keyword density limit
            revised_section = _enforce_keyword_density(
                original_section=section,
                revised_section=revised_section,
                jd_keywords=all_keywords,
            )

            # Post-process: reorder entries if allowed and beneficial
            if not settings.no_reordering and settings.aggressiveness != "conservative":
                revised_section = _maybe_reorder_entries(
                    revised_section, all_keywords, settings.aggressiveness
                )

            edited_sections.append(revised_section)

        # Section-level reordering (aggressive only, if not disabled)
        if (
            settings.aggressiveness == "aggressive"
            and not settings.no_reordering
        ):
            edited_sections = _reorder_sections(edited_sections, all_keywords)

        return ResumeIR(
            source_format=ir.source_format,
            sections=edited_sections,
            metadata=ir.metadata,
            contact_info=ir.contact_info,
            has_tables=ir.has_tables,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _section_needs_editing(
    section: ResumeSection, keywords: List[str], aggressiveness: str
) -> bool:
    """Return True if the section has bullets that warrant editing."""
    threshold = {"conservative": 0.30, "balanced": 0.50, "aggressive": 0.0}.get(
        aggressiveness, 0.50
    )
    if aggressiveness == "aggressive":
        return True

    all_bullets = [b for e in section.entries for b in e.bullets] + section.plain_items
    if not all_bullets:
        return False

    low_overlap = [
        b for b in all_bullets
        if _keyword_overlap(b.text, keywords) < threshold
    ]
    return len(low_overlap) > 0


def _preserve_immutable_fields(
    original: ResumeSection, revised: ResumeSection
) -> ResumeSection:
    """
    Copy employer, title, dates, location from original entries into revised.
    Also ensure section heading is unchanged.
    """
    revised.heading = original.heading
    revised.heading_style = original.heading_style

    # Build lookup by entry id
    orig_by_id = {e.id: e for e in original.entries}

    for rev_entry in revised.entries:
        orig_entry = orig_by_id.get(rev_entry.id)
        if orig_entry:
            rev_entry.employer = orig_entry.employer
            rev_entry.title = orig_entry.title
            rev_entry.start_date = orig_entry.start_date
            rev_entry.end_date = orig_entry.end_date
            rev_entry.location = orig_entry.location

    return revised


def _enforce_keyword_density(
    original_section: ResumeSection,
    revised_section: ResumeSection,
    jd_keywords: List[str],
    max_new_keywords: int = 3,
) -> ResumeSection:
    """
    For each bullet in the revised section, if it added more than max_new_keywords
    new keywords compared to the original, revert to the original bullet text.
    """
    orig_bullets: Dict[str, BulletItem] = {}
    for entry in original_section.entries:
        for b in entry.bullets:
            orig_bullets[b.id] = b
    for b in original_section.plain_items:
        orig_bullets[b.id] = b

    def check_bullet(rev_b: BulletItem) -> BulletItem:
        orig_b = orig_bullets.get(rev_b.id)
        if not orig_b:
            return rev_b
        orig_kws = _tokenize(orig_b.text) & {k.lower() for k in jd_keywords}
        rev_kws = _tokenize(rev_b.text) & {k.lower() for k in jd_keywords}
        new_kws = rev_kws - orig_kws
        if len(new_kws) > max_new_keywords:
            return orig_b  # revert
        return rev_b

    for entry in revised_section.entries:
        entry.bullets = [check_bullet(b) for b in entry.bullets]
    revised_section.plain_items = [check_bullet(b) for b in revised_section.plain_items]

    return revised_section


def _maybe_reorder_entries(
    section: ResumeSection,
    keywords: List[str],
    aggressiveness: str,
) -> ResumeSection:
    """Reorder entries within a section by relevance if beneficial."""
    if len(section.entries) < 2:
        return section

    scored = [
        (entry, _entry_relevance(entry, keywords)) for entry in section.entries
    ]
    # Only reorder experience sections and only if top entry is not already highest
    max_score = max(s for _, s in scored)
    current_top_score = scored[0][1]

    if aggressiveness == "aggressive" and max_score > current_top_score:
        section.entries = [e for e, _ in sorted(scored, key=lambda x: -x[1])]
    elif aggressiveness == "balanced" and max_score > current_top_score * 1.5:
        # Only reorder if there's a significant improvement
        section.entries = [e for e, _ in sorted(scored, key=lambda x: -x[1])]

    return section


def _reorder_sections(
    sections: List[ResumeSection], keywords: List[str]
) -> List[ResumeSection]:
    """
    Aggressive mode: move relevant experience/skills sections toward the top,
    keeping contact/summary at the very top.
    """
    pinned = [s for s in sections if s.section_type in ("summary",)]
    experience = [s for s in sections if s.section_type == "experience"]
    skills = [s for s in sections if s.section_type == "skills"]
    rest = [
        s for s in sections
        if s.section_type not in ("summary", "experience", "skills")
    ]
    return pinned + experience + skills + rest
