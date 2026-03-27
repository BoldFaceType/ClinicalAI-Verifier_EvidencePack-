from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from support import cleanup_temp_dir, make_temp_dir

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_packer.pipeline import run_packaging


class EvidencePackerTests(unittest.TestCase):
    def test_run_packaging_creates_appeal_packet_for_denial(self) -> None:
        temp_path = make_temp_dir("evidence_denial")
        try:
            claim_response_json = temp_path / "claimresponse_denied.json"
            notes_dir = temp_path / "clinical_notes"
            output_dir = temp_path / "out"
            notes_dir.mkdir()
            claim_response_json.write_text(
                json.dumps(
                    {
                        "resourceType": "ClaimResponse",
                        "outcome": "error",
                        "disposition": "Authorization missing for imaging request.",
                        "item": [
                            {
                                "adjudication": [
                                    {
                                        "reason": {
                                            "coding": [{"code": "AUTH-001"}],
                                            "text": "Missing authorization",
                                        }
                                    }
                                ]
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (notes_dir / "note_1.txt").write_text(
                "Prior auth was approved on 2025-08-10. Referral number is documented in the chart.",
                encoding="utf-8",
            )
            summary = run_packaging(claim_response_json, notes_dir, output_dir)
            self.assertEqual(summary["status"], "appeal_packet_generated")
            self.assertEqual(summary["denial_code"], "AUTH-001")
            self.assertEqual(summary["strategy_category"], "prior_auth_missing")
            packet = json.loads((output_dir / "packet.json").read_text(encoding="utf-8"))
            self.assertTrue(packet["appeal_ready"])
            self.assertEqual(packet["strategy_category"], "prior_auth_missing")
            self.assertTrue((output_dir / "appeal_packet.pdf").exists())
        finally:
            cleanup_temp_dir(temp_path)

    def test_run_packaging_returns_no_action_for_non_denial_outcome(self) -> None:
        temp_path = make_temp_dir("evidence_no_action")
        try:
            claim_response_json = temp_path / "claimresponse_paid.json"
            notes_dir = temp_path / "clinical_notes"
            output_dir = temp_path / "out"
            notes_dir.mkdir()
            claim_response_json.write_text(
                json.dumps(
                    {
                        "resourceType": "ClaimResponse",
                        "outcome": "complete",
                        "disposition": "Claim paid in full.",
                        "item": [],
                    }
                ),
                encoding="utf-8",
            )
            summary = run_packaging(claim_response_json, notes_dir, output_dir)
            self.assertEqual(summary["status"], "no_action")
            self.assertFalse(summary["output_generated"])
        finally:
            cleanup_temp_dir(temp_path)

    def test_run_packaging_rejects_non_claim_response_inputs(self) -> None:
        temp_path = make_temp_dir("evidence_invalid")
        try:
            claim_response_json = temp_path / "bad.json"
            notes_dir = temp_path / "clinical_notes"
            output_dir = temp_path / "out"
            notes_dir.mkdir()
            claim_response_json.write_text(
                json.dumps({"resourceType": "Observation"}), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                run_packaging(claim_response_json, notes_dir, output_dir)
        finally:
            cleanup_temp_dir(temp_path)


if __name__ == "__main__":
    unittest.main()
