from __future__ import annotations

from evidence_packer.models.fhir_models import ClaimResponseModel, DenialDecision


def parse_denial_reason(model: ClaimResponseModel) -> DenialDecision:
    primary_reason = model.reasons[0] if model.reasons else None
    denial_code = primary_reason.code if primary_reason and primary_reason.code else "UNKNOWN"
    denial_text = (
        primary_reason.text
        if primary_reason and primary_reason.text
        else model.disposition or "No denial text provided."
    )
    return DenialDecision(
        denial_code=denial_code,
        denial_text=denial_text,
        outcome=model.outcome.lower(),
        disposition=model.disposition,
    )
