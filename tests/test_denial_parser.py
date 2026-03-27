from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_packer.handler.denial_handler import should_continue
from evidence_packer.handler.parser import parse_denial_reason
from evidence_packer.models.fhir_models import parse_claim_response


class DenialParserTests(unittest.TestCase):
    def test_parse_claim_response_and_denial_summary(self) -> None:
        sample_path = Path(__file__).resolve().parents[1] / "samples" / "claimresponse_denied.json"
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        model = parse_claim_response(payload)
        decision = parse_denial_reason(model)
        self.assertEqual(model.resource_type, "ClaimResponse")
        self.assertTrue(should_continue(model))
        self.assertEqual(decision.denial_code, "AUTH-001")
        self.assertIn("authorization", decision.denial_text.lower())
        self.assertEqual(decision.outcome, "error")


if __name__ == "__main__":
    unittest.main()
