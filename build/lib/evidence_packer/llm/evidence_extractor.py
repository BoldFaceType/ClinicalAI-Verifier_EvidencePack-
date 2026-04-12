from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field

from evidence_packer.models.fhir_models import ClinicalNote, EvidenceExcerpt
from evidence_packer.strategy.evidence_mapper import EvidencePlan


class SupportsResponses(Protocol):
    def create(self, *args: Any, **kwargs: Any) -> Any: ...


@dataclass
class InstructorClientAdapter:
    client: Any

    def create(self, *args: Any, **kwargs: Any) -> Any:
        return self.client.chat.completions.create(*args, **kwargs)


class EvidenceExtractionResponse(BaseModel):
    excerpts: list[str] = Field(default_factory=list)


def extract_supporting_evidence(
    notes: list[ClinicalNote],
    plan: EvidencePlan,
    denial_text: str,
    *,
    use_ai: bool = False,
    client: SupportsResponses | None = None,
) -> list[EvidenceExcerpt]:
    if use_ai:
        ai_excerpts = _extract_with_instructor(notes, plan, denial_text, client=client)
        if ai_excerpts:
            return ai_excerpts

    excerpts: list[EvidenceExcerpt] = []
    denial_terms = {term.lower() for term in denial_text.replace("/", " ").split() if len(term) > 3}
    for note in notes:
        best_excerpt = ""
        best_score = 0.0
        for sentence in _split_sentences(note.text):
            sentence_terms = sentence.lower()
            score = 0.0
            for term in plan.search_terms:
                if term.lower() in sentence_terms:
                    score += 0.25
            for term in denial_terms:
                if term in sentence_terms:
                    score += 0.1
            if score > best_score:
                best_score = score
                best_excerpt = sentence.strip()
        if best_excerpt:
            excerpts.append(
                EvidenceExcerpt(
                    source=note.source,
                    excerpt=best_excerpt,
                    confidence=min(round(best_score, 2), 0.99),
                )
            )
    excerpts.sort(key=lambda item: (-item.confidence, item.source, item.excerpt))
    return excerpts


def _extract_with_instructor(
    notes: list[ClinicalNote],
    plan: EvidencePlan,
    denial_text: str,
    *,
    client: SupportsResponses | None = None,
) -> list[EvidenceExcerpt]:
    active_client = client or _build_instructor_client()
    if active_client is None:
        return []

    excerpts: list[EvidenceExcerpt] = []
    for note in notes:
        response = active_client.create(
            model="gpt-4.1-mini",
            response_model=EvidenceExtractionResponse,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract the most relevant supporting evidence sentences for an appeal packet. "
                        "Return only verbatim excerpts from the provided note."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Denial text: {denial_text}\n"
                        f"Evidence strategy: {plan.category}\n"
                        f"Search terms: {', '.join(plan.search_terms)}\n"
                        f"Clinical note:\n{note.text}"
                    ),
                },
            ],
        )
        for excerpt in response.excerpts[:3]:
            cleaned = excerpt.strip()
            if cleaned:
                excerpts.append(
                    EvidenceExcerpt(source=note.source, excerpt=cleaned, confidence=0.95)
                )
    excerpts.sort(key=lambda item: (-item.confidence, item.source, item.excerpt))
    return excerpts


def _build_instructor_client() -> SupportsResponses | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        import instructor
        from openai import OpenAI
    except ImportError:
        return None
    return InstructorClientAdapter(client=instructor.from_openai(OpenAI()))


def _split_sentences(text: str) -> list[str]:
    normalized = text.replace("\n", " ")
    sentences = [part.strip() for part in normalized.split(".") if part.strip()]
    return sentences or [normalized.strip()]
