from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_packer.llm.evidence_extractor import (
    EvidenceExtractionResponse,
    extract_supporting_evidence,
)
from evidence_packer.models.fhir_models import ClinicalNote
from evidence_packer.strategy.evidence_mapper import EvidencePlan


class FakeInstructorClient:
    def create(self, *args, **kwargs) -> EvidenceExtractionResponse:
        return EvidenceExtractionResponse(
            excerpts=["Authorization approval is documented in the chart."]
        )


class EvidenceExtractorTests(unittest.TestCase):
    def test_instructor_path_returns_structured_excerpts(self) -> None:
        notes = [
            ClinicalNote(
                source="note.txt",
                text="Authorization approval is documented in the chart.",
            )
        ]
        plan = EvidencePlan(
            category="prior_auth_missing",
            required_documents=["authorization"],
            search_terms=["authorization", "prior auth"],
        )
        excerpts = extract_supporting_evidence(
            notes,
            plan,
            "Missing authorization",
            use_ai=True,
            client=FakeInstructorClient(),
        )
        self.assertEqual(len(excerpts), 1)
        self.assertEqual(excerpts[0].confidence, 0.95)

    def test_instructor_path_falls_back_to_heuristics(self) -> None:
        notes = [
            ClinicalNote(
                source="note.txt",
                text="Prior auth was approved yesterday. Referral number is in the chart.",
            )
        ]
        plan = EvidencePlan(
            category="prior_auth_missing",
            required_documents=["authorization"],
            search_terms=["authorization", "prior auth"],
        )
        excerpts = extract_supporting_evidence(notes, plan, "Missing authorization", use_ai=True)
        self.assertGreaterEqual(len(excerpts), 1)


if __name__ == "__main__":
    unittest.main()
