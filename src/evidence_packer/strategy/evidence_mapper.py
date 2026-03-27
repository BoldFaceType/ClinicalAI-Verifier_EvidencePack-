from __future__ import annotations

from dataclasses import dataclass

from evidence_packer.models.fhir_models import DenialDecision


@dataclass(frozen=True)
class EvidencePlan:
    category: str
    required_documents: list[str]
    search_terms: list[str]


def resolve_evidence_strategy(decision: DenialDecision) -> EvidencePlan:
    text = f"{decision.denial_code} {decision.denial_text}".lower()
    if "auth" in text or "authorization" in text or "prior auth" in text:
        return EvidencePlan(
            category="prior_auth_missing",
            required_documents=["authorization", "denial_letter", "claim_summary"],
            search_terms=["authorization", "approved", "prior auth", "referral"],
        )
    if "necess" in text or "clinical" in text:
        return EvidencePlan(
            category="medical_necessity",
            required_documents=["clinical_notes", "denial_letter", "claim_summary"],
            search_terms=["medical necessity", "symptoms", "assessment", "plan"],
        )
    return EvidencePlan(
        category="conservative_therapy_missing",
        required_documents=["pt_notes", "pcp_notes", "medication_history"],
        search_terms=["physical therapy", "conservative", "medication", "PCP"],
    )
