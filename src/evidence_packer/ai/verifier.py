from __future__ import annotations

from evidence_packer.ai.contracts import (
    CandidateEvidence,
    EvidenceVerificationResult,
    RejectedEvidence,
    VerifiedEvidence,
)
from evidence_packer.models.fhir_models import ClinicalNote


def verify_candidate_evidence(
    candidates: list[CandidateEvidence],
    notes: list[ClinicalNote],
) -> EvidenceVerificationResult:
    notes_by_source = {note.source: note for note in notes}
    verified: list[VerifiedEvidence] = []
    rejected: list[RejectedEvidence] = []

    for candidate in candidates:
        quote = candidate.quote.strip()
        source = candidate.source.strip()
        note = notes_by_source.get(source)
        if note is None:
            rejected.append(
                _reject(candidate, "rejected_source_not_found")
            )
            continue
        if not quote:
            rejected.append(_reject(candidate, "rejected_empty_quote"))
            continue
        if quote not in note.text:
            rejected.append(_reject(candidate, "rejected_quote_not_found"))
            continue
        verified.append(
            VerifiedEvidence(
                source=source,
                excerpt=quote,
                confidence=_clamp_confidence(candidate.confidence),
                rationale=candidate.rationale.strip(),
            )
        )

    verified.sort(key=lambda item: (-item.confidence, item.source, item.excerpt))
    rejected.sort(key=lambda item: (item.source, item.quote, item.verification_status))
    return EvidenceVerificationResult(verified=verified, rejected=rejected)


def _reject(candidate: CandidateEvidence, status: str) -> RejectedEvidence:
    return RejectedEvidence(
        source=candidate.source.strip(),
        quote=candidate.quote.strip(),
        rationale=candidate.rationale.strip(),
        confidence=_clamp_confidence(candidate.confidence),
        verification_status=status,
    )


def _clamp_confidence(value: float) -> float:
    return min(max(round(float(value), 2), 0.0), 0.99)

