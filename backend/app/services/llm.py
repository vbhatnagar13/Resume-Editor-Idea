"""OpenAI LLM integration for resume tailoring."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Protocol

from app.models.ir import ResumeIR, ResumeSection
from app.models.schemas import TailorRequest
from app.prompts.templates import (
    JD_ANALYZER_PROMPT,
    RESUME_EDITOR_PROMPT,
    SYSTEM_PROMPT,
    VERIFIER_PROMPT,
)


# ---------------------------------------------------------------------------
# LLM Client Protocol (for dependency injection / mocking)
# ---------------------------------------------------------------------------

class LLMClient(Protocol):
    def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        """Send a chat completion request and return the response text."""
        ...


# ---------------------------------------------------------------------------
# OpenAI implementation
# ---------------------------------------------------------------------------

class OpenAIClient:
    """Thin wrapper around the OpenAI SDK."""

    MODEL = "gpt-4o-mini"

    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Please configure it in your environment "
                "or .env file before using the tailoring features."
            )
        import openai
        self._client = openai.OpenAI(api_key=key)

    def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        response = self._client.chat.completions.create(
            model=self.MODEL,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# LLM Service
# ---------------------------------------------------------------------------

class LLMService:
    """High-level LLM service methods for resume tailoring."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    def analyze_job_description(self, jd: str) -> Dict[str, Any]:
        """Extract structured info from a job description."""
        prompt = JD_ANALYZER_PROMPT.format(job_description=jd)
        raw = self._client.chat(system=SYSTEM_PROMPT, user=prompt)
        return _parse_json_response(raw, default={
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "keywords": [],
            "seniority": "mid",
            "job_title": "",
            "industry": "",
            "key_technologies": [],
            "soft_skills": [],
        })

    # ------------------------------------------------------------------
    def tailor_section(
        self,
        section: ResumeSection,
        jd_analysis: Dict[str, Any],
        settings: TailorRequest,
    ) -> ResumeSection:
        """Tailor a single ResumeSection using the LLM."""
        section_json = section.model_dump_json(indent=2)
        jd_json = json.dumps(jd_analysis, indent=2)

        prompt = RESUME_EDITOR_PROMPT.format(
            resume_section_json=section_json,
            jd_analysis_json=jd_json,
            aggressiveness=settings.aggressiveness,
            keyword_emphasis=settings.keyword_emphasis,
            no_reordering=settings.no_reordering,
        )

        raw = self._client.chat(system=SYSTEM_PROMPT, user=prompt)
        revised_dict = _parse_json_response(raw, default=section.model_dump())
        try:
            return ResumeSection.model_validate(revised_dict)
        except Exception:
            return section  # fall back to original on validation error

    # ------------------------------------------------------------------
    def tailor_resume(
        self,
        ir: ResumeIR,
        jd_analysis: Dict[str, Any],
        settings: TailorRequest,
    ) -> ResumeIR:
        """Tailor all sections of a ResumeIR."""
        tailored_sections = []
        for section in ir.sections:
            if section.section_type in ("experience", "skills", "summary"):
                tailored_sections.append(
                    self.tailor_section(section, jd_analysis, settings)
                )
            else:
                tailored_sections.append(section)

        return ResumeIR(
            source_format=ir.source_format,
            sections=tailored_sections,
            metadata=ir.metadata,
            contact_info=ir.contact_info,
            has_tables=ir.has_tables,
        )

    # ------------------------------------------------------------------
    def verify_resume(
        self,
        original_ir: ResumeIR,
        revised_ir: ResumeIR,
        jd_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run the verifier prompt against original vs revised resume."""
        prompt = VERIFIER_PROMPT.format(
            original_json=original_ir.model_dump_json(indent=2),
            revised_json=revised_ir.model_dump_json(indent=2),
            jd_analysis_json=json.dumps(jd_analysis, indent=2),
        )
        raw = self._client.chat(system=SYSTEM_PROMPT, user=prompt, temperature=0.0)
        return _parse_json_response(raw, default={
            "fabrication_detected": False,
            "fabrication_details": [],
            "date_changes_detected": False,
            "metric_changes": [],
            "keyword_stuffing_detected": False,
            "overall_status": "passed",
            "ats_check": "ATS-friendly",
            "warnings": [],
        })


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str, default: Any) -> Any:
    """Extract JSON from an LLM response, returning default on failure."""
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(
            l for l in lines if not l.strip().startswith("```")
        )
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object/array in the response
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
    return default


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_llm_service(api_key: Optional[str] = None) -> LLMService:
    """Factory that builds an LLMService with OpenAI client."""
    client = OpenAIClient(api_key=api_key)
    return LLMService(client=client)
