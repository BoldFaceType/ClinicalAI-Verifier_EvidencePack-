from __future__ import annotations

from evidence_packer.models.fhir_models import ClaimResponseModel, DenialDecision, DenialReason


def parse_denial_reason(model: ClaimResponseModel) -> DenialDecision:
    primary_reason = _select_primary_reason(model)
    denial_code = _resolve_denial_code(primary_reason.code if primary_reason else "", primary_reason.text if primary_reason else "", model.disposition)
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


def _select_primary_reason(model: ClaimResponseModel) -> DenialReason | None:
    if not model.reasons:
        return None
    return max(model.reasons, key=lambda reason: _score_reason(f"{reason.code} {reason.text}"))


def _score_reason(text: str) -> int:
    normalized = text.lower()
    score = 0
    for token, weight in {
        "auth": 6,
        "authorization": 6,
        "necess": 5,
        "medical": 4,
        "clinical": 4,
        "coverage": 3,
        "noncovered": 3,
        "denied": 2,
    }.items():
        if token in normalized:
            score += weight
    return score


def _resolve_denial_code(code: str, text: str, disposition: str) -> str:
    if code:
        return code
    normalized = f"{text} {disposition}".lower()
    if "auth" in normalized:
        return "AUTH-UNSPECIFIED"
    if "necess" in normalized or "clinical" in normalized:
        return "MED-NECESSITY-UNSPECIFIED"
    return "UNKNOWN"
