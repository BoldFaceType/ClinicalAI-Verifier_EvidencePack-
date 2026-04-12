from __future__ import annotations

from dataclasses import dataclass

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    BaseModel = None
    ConfigDict = None
    Field = None


@dataclass(frozen=True)
class DenialReason:
    code: str
    text: str


@dataclass(frozen=True)
class DenialDecision:
    denial_code: str
    denial_text: str
    outcome: str
    disposition: str


@dataclass(frozen=True)
class ClinicalNote:
    source: str
    text: str


@dataclass(frozen=True)
class NoteDocument:
    source: str
    text: str


@dataclass(frozen=True)
class EvidenceExcerpt:
    source: str
    excerpt: str
    confidence: float


@dataclass(frozen=True)
class EvidenceStrategy:
    category: str
    required_documents: list[str]
    search_terms: list[str]

    @property
    def evidence_types(self) -> list[str]:
        return self.required_documents


@dataclass(frozen=True)
class Adjudication:
    reason_code: str
    reason_text: str


@dataclass(frozen=True)
class ClaimResponseItem:
    adjudications: list[Adjudication]


@dataclass(frozen=True)
class ClaimResponse:
    resource_type: str
    claim_id: str
    outcome: str
    disposition: str
    items: list[ClaimResponseItem]
    reasons: list[DenialReason]


ClaimResponseModel = ClaimResponse


if BaseModel is not None:

    class CodingModel(BaseModel):
        model_config = ConfigDict(extra="ignore")
        code: str = ""
        display: str = ""

    class ReasonModel(BaseModel):
        model_config = ConfigDict(extra="ignore")
        coding: list[CodingModel] = Field(default_factory=list)
        text: str = ""

    class AdjudicationModel(BaseModel):
        model_config = ConfigDict(extra="ignore")
        reason: ReasonModel = Field(default_factory=ReasonModel)

    class ClaimItemModel(BaseModel):
        model_config = ConfigDict(extra="ignore")
        adjudication: list[AdjudicationModel] = Field(default_factory=list)

    class ClaimResponseEnvelope(BaseModel):
        model_config = ConfigDict(extra="ignore")
        resourceType: str = ""
        id: str = ""
        outcome: str = ""
        disposition: str = ""
        item: list[ClaimItemModel] = Field(default_factory=list)
else:
    ClaimResponseEnvelope = None


def parse_claim_response(payload: dict[str, object]) -> ClaimResponse:
    if ClaimResponseEnvelope is not None:
        envelope = ClaimResponseEnvelope.model_validate(payload)
        items = [
            ClaimResponseItem(
                adjudications=[
                    Adjudication(
                        reason_code=_extract_code_from_reason_model(adjudication.reason),
                        reason_text=_extract_text_from_reason_model(adjudication.reason),
                    )
                    for adjudication in item.adjudication
                    if _extract_code_from_reason_model(adjudication.reason)
                    or _extract_text_from_reason_model(adjudication.reason)
                ]
            )
            for item in envelope.item
        ]
        reasons = [
            DenialReason(code=adjudication.reason_code, text=adjudication.reason_text)
            for item in items
            for adjudication in item.adjudications
        ]
        return ClaimResponse(
            resource_type=envelope.resourceType,
            claim_id=envelope.id,
            outcome=envelope.outcome.lower(),
            disposition=envelope.disposition,
            items=items,
            reasons=reasons,
        )

    items: list[ClaimResponseItem] = []
    for raw_item in payload.get("item", []) or []:
        if not isinstance(raw_item, dict):
            continue
        adjudications: list[Adjudication] = []
        for raw_adjudication in raw_item.get("adjudication", []) or []:
            if not isinstance(raw_adjudication, dict):
                continue
            reason = raw_adjudication.get("reason", {})
            if not isinstance(reason, dict):
                continue
            reason_code = _extract_code(reason)
            reason_text = str(reason.get("text", "") or _extract_display(reason)).strip()
            if reason_code or reason_text:
                adjudications.append(
                    Adjudication(
                        reason_code=reason_code,
                        reason_text=reason_text,
                    )
                )
        items.append(ClaimResponseItem(adjudications=adjudications))

    reasons = [
        DenialReason(code=adjudication.reason_code, text=adjudication.reason_text)
        for item in items
        for adjudication in item.adjudications
    ]
    return ClaimResponse(
        resource_type=str(payload.get("resourceType", "") or ""),
        claim_id=str(payload.get("id", "") or ""),
        outcome=str(payload.get("outcome", "") or "").lower(),
        disposition=str(payload.get("disposition", "") or ""),
        items=items,
        reasons=reasons,
    )


def _extract_code(reason: dict[str, object]) -> str:
    coding = reason.get("coding", []) or []
    if isinstance(coding, list):
        for entry in coding:
            if isinstance(entry, dict) and entry.get("code"):
                return str(entry["code"]).strip()
    return str(reason.get("code", "") or "").strip()


def _extract_display(reason: dict[str, object]) -> str:
    coding = reason.get("coding", []) or []
    if isinstance(coding, list):
        for entry in coding:
            if isinstance(entry, dict) and entry.get("display"):
                return str(entry["display"]).strip()
    return str(reason.get("display", "") or "").strip()


def _extract_code_from_reason_model(reason: object) -> str:
    coding = getattr(reason, "coding", [])
    for entry in coding:
        code = getattr(entry, "code", "")
        if code:
            return str(code).strip()
    return ""


def _extract_text_from_reason_model(reason: object) -> str:
    text = getattr(reason, "text", "")
    if text:
        return str(text).strip()
    coding = getattr(reason, "coding", [])
    for entry in coding:
        display = getattr(entry, "display", "")
        if display:
            return str(display).strip()
    return ""
