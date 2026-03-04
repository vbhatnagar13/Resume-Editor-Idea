"""Diff report generator: compares original vs revised ResumeIR."""

from __future__ import annotations

from typing import List, Set

from app.models.ir import BulletItem, ResumeIR
from app.models.schemas import DiffChange, DiffReport


def generate_diff(original: ResumeIR, revised: ResumeIR) -> DiffReport:
    """Compare two ResumeIR objects and produce a DiffReport."""
    changes: List[DiffChange] = []
    keywords_added: List[str] = []
    keywords_preserved: List[str] = []
    sections_reordered: List[str] = []

    # Build lookup maps
    orig_sections = {s.id: s for s in original.sections}
    rev_sections = {s.id: s for s in revised.sections}

    # Check for section reordering
    orig_section_ids = [s.id for s in original.sections]
    rev_section_ids = [s.id for s in revised.sections]
    if orig_section_ids != rev_section_ids:
        for sid in rev_section_ids:
            if sid in orig_sections:
                orig_pos = orig_section_ids.index(sid)
                rev_pos = rev_section_ids.index(sid)
                if orig_pos != rev_pos:
                    sections_reordered.append(orig_sections[sid].heading)

    # Compare sections
    for section_id, rev_section in rev_sections.items():
        orig_section = orig_sections.get(section_id)
        if not orig_section:
            continue

        # Build bullet lookup per section
        orig_bullets = _collect_bullets(orig_section)
        rev_bullets = _collect_bullets(rev_section)

        orig_entry_ids = [e.id for e in orig_section.entries]
        rev_entry_ids = [e.id for e in rev_section.entries]
        if orig_entry_ids != rev_entry_ids:
            changes.append(
                DiffChange(
                    section=rev_section.heading,
                    entry_id=None,
                    bullet_id=None,
                    change_type="reorder",
                    original=", ".join(
                        e.employer or e.id for e in orig_section.entries
                    ),
                    revised=", ".join(
                        e.employer or e.id for e in rev_section.entries
                    ),
                    reason="Entries reordered for relevance",
                )
            )

        # Per-bullet diff
        for bid, orig_b in orig_bullets.items():
            rev_b = rev_bullets.get(bid)
            if not rev_b:
                continue
            if rev_b.text != orig_b.text:
                change_type = "rewrite"
                added_kws = _find_added_keywords(orig_b.text, rev_b.text)
                if added_kws:
                    change_type = "keyword_add"
                    keywords_added.extend(added_kws)

                changes.append(
                    DiffChange(
                        section=rev_section.heading,
                        entry_id=_find_entry_for_bullet(rev_section, bid),
                        bullet_id=bid,
                        change_type=change_type,
                        original=orig_b.text,
                        revised=rev_b.text,
                        reason="Bullet rewritten to align with job requirements",
                    )
                )
            else:
                # Preserved keywords
                from app.services.editor import _tokenize
                keywords_preserved.extend(list(_tokenize(orig_b.text))[:3])

    # Fabrication check
    fabrication_msg = _check_fabrication(original, revised)

    # ATS check
    ats_msg = _check_ats(original, revised)

    return DiffReport(
        changes=changes,
        keywords_added=list(dict.fromkeys(keywords_added)),  # deduplicate
        keywords_preserved=list(dict.fromkeys(keywords_preserved[:20])),
        sections_reordered=sections_reordered,
        fabrication_check=fabrication_msg,
        ats_check=ats_msg,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_bullets(section: "ResumeSection") -> dict:  # type: ignore[name-defined]
    bullets = {}
    for entry in section.entries:
        for b in entry.bullets:
            bullets[b.id] = b
    for b in section.plain_items:
        bullets[b.id] = b
    return bullets


def _find_entry_for_bullet(section: "ResumeSection", bullet_id: str) -> str | None:  # type: ignore[name-defined]
    for entry in section.entries:
        for b in entry.bullets:
            if b.id == bullet_id:
                return entry.id
    return None


def _find_added_keywords(original: str, revised: str) -> List[str]:
    """Find words present in revised but not in original (simple heuristic)."""
    import re
    orig_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", original.lower()))
    rev_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", revised.lower()))
    added = rev_words - orig_words
    # Filter common stop words
    stop = {
        "the", "and", "for", "with", "this", "that", "have", "from",
        "not", "are", "was", "were", "been", "will", "would", "could",
        "their", "they", "them", "than", "then", "also", "more", "into",
    }
    return [w for w in added if w not in stop]


def _check_fabrication(original: ResumeIR, revised: ResumeIR) -> str:
    """Check if any new employer/title/degree appeared in revised."""
    orig_employers: Set[str] = set()
    for s in original.sections:
        for e in s.entries:
            if e.employer:
                orig_employers.add(e.employer.lower().strip())

    for s in revised.sections:
        for e in s.entries:
            if e.employer:
                emp = e.employer.lower().strip()
                if emp and emp not in orig_employers:
                    return (
                        f"WARNING: New employer detected in revised resume: "
                        f"'{e.employer}'. This may be fabricated content."
                    )
    return "passed"


def _check_ats(original: ResumeIR, revised: ResumeIR) -> str:
    """Check for ATS-unfriendly elements introduced in the revised resume."""
    if not original.has_tables and revised.has_tables:
        return (
            "WARNING: Tables were added to the revised resume. "
            "Tables can reduce ATS compatibility."
        )
    return "ATS-friendly"
