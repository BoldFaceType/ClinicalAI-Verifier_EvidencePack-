from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CandidateEvidence:
    source: str
    quote: str
    rationale: str = ""
    confidence: float = 0.0


@dataclass(frozen=True)
class VerifiedEvidence:
    source: str
    excerpt: str
    confidence: float
    rationale: str
    verification_status: str = "verified"


@dataclass(frozen=True)
class RejectedEvidence:
    source: str
    quote: str
    rationale: str
    confidence: float
    verification_status: str


@dataclass(frozen=True)
class EvidenceVerificationResult:
    verified: list[VerifiedEvidence] = field(default_factory=list)
    rejected: list[RejectedEvidence] = field(default_factory=list)

    def to_audit_dict(self) -> dict[str, object]:
        return {
            "verified_evidence_count": len(self.verified),
            "rejected_evidence_count": len(self.rejected),
            "verified": [item.__dict__ for item in self.verified],
            "rejected": [item.__dict__ for item in self.rejected],
        }

