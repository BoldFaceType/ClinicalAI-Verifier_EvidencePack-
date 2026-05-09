from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field

from evidence_packer.ai.contracts import CandidateEvidence, EvidenceVerificationResult
from evidence_packer.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from evidence_packer.ai.verifier import verify_candidate_evidence
from evidence_packer.models.fhir_models import ClinicalNote, EvidenceExcerpt
from evidence_packer.strategy.evidence_mapper import EvidencePlan


class SupportsResponses(Protocol):
    def create(self, *args: Any, **kwargs: Any) -> Any: ...


@dataclass
class OpenAIClientAdapter:
    client: Any
    model: str | None = None

    def create(self, *args: Any, **kwargs: Any) -> Any:
        kwargs.pop("response_model", None)
        if self.model:
            kwargs["model"] = self.model
        kwargs.setdefault("response_format", {"type": "json_object"})
        response = self.client.chat.completions.create(*args, **kwargs)
        content = response.choices[0].message.content or "{}"
        return EvidenceExtractionResponse.model_validate(json.loads(content))


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
    excerpts, _audit = extract_supporting_evidence_with_audit(
        notes,
        plan,
        denial_text,
        use_ai=use_ai,
        client=client,
    )
    return excerpts


def extract_supporting_evidence_with_audit(
    notes: list[ClinicalNote],
    plan: EvidencePlan,
    denial_text: str,
    *,
    use_ai: bool = False,
    client: SupportsResponses | None = None,
) -> tuple[list[EvidenceExcerpt], EvidenceVerificationResult | None]:
    if use_ai:
        ai_excerpts, audit = _extract_with_instructor(notes, plan, denial_text, client=client)
        if audit is not None:
            return ai_excerpts, audit

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
    return excerpts, None


def _extract_with_instructor(
    notes: list[ClinicalNote],
    plan: EvidencePlan,
    denial_text: str,
    *,
    client: SupportsResponses | None = None,
) -> tuple[list[EvidenceExcerpt], EvidenceVerificationResult | None]:
    active_client = client or _build_instructor_client()
    if active_client is None:
        return [], None

    candidates: list[CandidateEvidence] = []
    for note in notes:
        response = active_client.create(
            model="gpt-4.1-mini",
            response_model=EvidenceExtractionResponse,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": build_user_prompt(
                        denial_text=denial_text,
                        strategy_category=plan.category,
                        search_terms=plan.search_terms,
                        note_text=note.text,
                    ),
                },
            ],
        )
        for excerpt in response.excerpts[:3]:
            cleaned = excerpt.strip()
            if cleaned:
                candidates.append(
                    CandidateEvidence(
                        source=note.source,
                        quote=cleaned,
                        rationale=f"AI-selected evidence for {plan.category}.",
                        confidence=0.95,
                    )
                )
    audit = verify_candidate_evidence(candidates, notes)
    excerpts = [
        EvidenceExcerpt(source=item.source, excerpt=item.excerpt, confidence=item.confidence)
        for item in audit.verified
    ]
    excerpts.sort(key=lambda item: (-item.confidence, item.source, item.excerpt))
    return excerpts, audit


def _build_instructor_client() -> SupportsResponses | None:
    try:
        from openai import AzureOpenAI, OpenAI
    except ImportError:
        return None

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if azure_endpoint and azure_key and azure_deployment:
        return OpenAIClientAdapter(
            client=AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            ),
            model=azure_deployment,
        )

    if os.getenv("OPENAI_API_KEY"):
        return OpenAIClientAdapter(
            client=OpenAI(),
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        )
    return None


def _split_sentences(text: str) -> list[str]:
    normalized = text.replace("\n", " ")
    sentences = [part.strip() for part in normalized.split(".") if part.strip()]
    return sentences or [normalized.strip()]
