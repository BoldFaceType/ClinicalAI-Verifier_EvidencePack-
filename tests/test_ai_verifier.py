from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_packer.ai.contracts import CandidateEvidence
from evidence_packer.ai.verifier import verify_candidate_evidence
from evidence_packer.models.fhir_models import ClinicalNote


class AIEvidenceVerifierTests(unittest.TestCase):
    def test_accepts_candidate_when_quote_exists_verbatim_in_source_note(self) -> None:
        notes = [
            ClinicalNote(
                source="note_1.txt",
                text="Prior authorization was approved on 2025-08-10. Referral number PA-123.",
            )
        ]
        candidate = CandidateEvidence(
            source="note_1.txt",
            quote="Prior authorization was approved on 2025-08-10.",
            rationale="Supports missing authorization appeal.",
            confidence=0.91,
        )

        result = verify_candidate_evidence([candidate], notes)

        self.assertEqual(len(result.verified), 1)
        self.assertEqual(result.verified[0].excerpt, candidate.quote)
        self.assertEqual(result.verified[0].verification_status, "verified")
        self.assertEqual(result.rejected, [])

    def test_rejects_candidate_when_quote_is_not_verbatim_in_source_note(self) -> None:
        notes = [
            ClinicalNote(
                source="note_1.txt",
                text="Prior authorization was requested but no approval number is present.",
            )
        ]
        candidate = CandidateEvidence(
            source="note_1.txt",
            quote="Prior authorization was approved on 2025-08-10.",
            rationale="Model inferred approval from the note.",
            confidence=0.91,
        )

        result = verify_candidate_evidence([candidate], notes)

        self.assertEqual(result.verified, [])
        self.assertEqual(len(result.rejected), 1)
        self.assertEqual(result.rejected[0].verification_status, "rejected_quote_not_found")


if __name__ == "__main__":
    unittest.main()
