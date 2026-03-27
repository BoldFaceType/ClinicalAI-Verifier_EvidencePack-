from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_packer.handler.parser import parse_denial_reason
from evidence_packer.models.fhir_models import parse_claim_response
from evidence_packer.strategy.evidence_mapper import resolve_evidence_strategy


class StrategyMapperTests(unittest.TestCase):
    def test_prior_auth_denial_maps_to_prior_auth_strategy(self) -> None:
        sample_path = Path(__file__).resolve().parents[1] / "samples" / "claimresponse_denied.json"
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        decision = parse_denial_reason(parse_claim_response(payload))
        strategy = resolve_evidence_strategy(decision)
        self.assertEqual(strategy.category, "prior_auth_missing")
        self.assertIn("authorization", strategy.required_documents)
        self.assertIn("prior auth", " ".join(strategy.search_terms).lower())


if __name__ == "__main__":
    unittest.main()
