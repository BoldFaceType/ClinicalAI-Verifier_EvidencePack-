from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from support import cleanup_temp_dir, make_temp_dir

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_packer.pipeline import run_packaging


class PacketGeneratorTests(unittest.TestCase):
    def test_pipeline_generates_packet_outputs(self) -> None:
        sample_claim = Path(__file__).resolve().parents[1] / "samples" / "claimresponse_denied.json"
        sample_notes = Path(__file__).resolve().parents[1] / "samples" / "clinical_notes"
        temp_path = make_temp_dir("packet_generator")
        try:
            output_dir = temp_path / "out"
            summary = run_packaging(sample_claim, sample_notes, output_dir)
            self.assertTrue(summary["output_generated"])
            self.assertEqual(summary["status"], "appeal_packet_generated")
            self.assertGreaterEqual(summary["excerpt_count"], 1)
            packet_json = output_dir / "packet.json"
            packet_pdf = output_dir / "appeal_packet.pdf"
            self.assertTrue(packet_json.exists())
            self.assertTrue(packet_pdf.exists())
            packet = json.loads(packet_json.read_text(encoding="utf-8"))
            self.assertEqual(packet["contract_version"], "evidence.packet.v1")
            self.assertEqual(packet["denial_code"], "AUTH-001")
            self.assertEqual(packet["strategy_category"], "prior_auth_missing")
            self.assertGreaterEqual(len(packet["evidence_excerpts"]), 1)
            self.assertIn(packet["pdf_renderer"], {"reportlab", "builtin_minimal"})
        finally:
            cleanup_temp_dir(temp_path)


if __name__ == "__main__":
    unittest.main()
