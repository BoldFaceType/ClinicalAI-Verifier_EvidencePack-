from __future__ import annotations

from evidence_packer.models.fhir_models import ClaimResponseModel

DENIAL_OUTCOMES = {"error", "partial"}


def should_continue(model: ClaimResponseModel) -> bool:
    return model.outcome.lower() in DENIAL_OUTCOMES


def detect_denial(model: ClaimResponseModel) -> bool:
    return should_continue(model)
