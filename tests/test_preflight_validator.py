from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path

from support import cleanup_temp_dir, make_temp_dir

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preflight_validator.pipeline import run_validation


class PreflightValidatorTests(unittest.TestCase):
    def test_run_validation_emits_json_and_markdown_reports(self) -> None:
        temp_path = make_temp_dir("preflight_reports")
        try:
            input_csv = temp_path / "dsfe.csv"
            output_dir = temp_path / "out"
            input_csv.write_text(
                "\n".join(
                    [
                        "member_id,measure_id,screening_date,screening_tool,screening_score,screening_loinc,follow_up_code,follow_up_date,bipolar_history,prior_year_depression_dx,source_kind",
                        "M-100,DSF-E,2025-04-01,PHQ-9,12,44261-6,96127,2025-04-10,0,0,structured",
                        "M-200,DSF-E,2025-05-01,PHQ-2,4,99999-9,,2025-06-20,yes,0,free_text",
                    ]
                ),
                encoding="utf-8",
            )
            summary = run_validation(input_csv, output_dir)
            self.assertEqual(summary["contract_version"], "preflight.summary.v1")
            self.assertEqual(summary["records_processed"], 2)
            self.assertEqual(summary["error_count"], 4)
            self.assertEqual(summary["warning_count"], 1)
            findings = json.loads((output_dir / "findings.json").read_text(encoding="utf-8"))
            rule_ids = {finding["rule_id"] for finding in findings["findings"]}
            self.assertIn("FR3_INVALID_LOINC", rule_ids)
            self.assertIn("FR5_FOLLOW_UP_OUTSIDE_WINDOW", rule_ids)
            self.assertIn("FR6_MEMBER_EXCLUDED_BIPOLAR_HISTORY", rule_ids)
        finally:
            cleanup_temp_dir(temp_path)

    def test_run_validation_supports_ndjson(self) -> None:
        temp_path = make_temp_dir("preflight_ndjson")
        try:
            input_file = temp_path / "dsfe.ndjson"
            output_dir = temp_path / "out"
            input_file.write_text(
                json.dumps(
                    {
                        "member_id": "M-1",
                        "measure_id": "DSF-E",
                        "screening_date": "2025-03-01",
                        "screening_tool": "PHQ-2",
                        "screening_score": "2",
                        "screening_loinc": "44249-1",
                        "follow_up_code": "",
                        "follow_up_date": "",
                        "bipolar_history": "0",
                        "prior_year_depression_dx": "0",
                        "source_kind": "structured",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            summary = run_validation(input_file, output_dir)
            self.assertEqual(summary["input_format"], "ndjson")
            self.assertEqual(summary["finding_count"], 0)
        finally:
            cleanup_temp_dir(temp_path)

    def test_run_validation_fails_when_required_fields_are_missing(self) -> None:
        temp_path = make_temp_dir("preflight_missing_fields")
        try:
            input_csv = temp_path / "invalid.csv"
            output_dir = temp_path / "out"
            input_csv.write_text("member_id,measure_id\nM-1,DSF-E\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                run_validation(input_csv, output_dir)
        finally:
            cleanup_temp_dir(temp_path)

    def test_run_validation_fails_when_ndjson_record_is_missing_required_field(self) -> None:
        temp_path = make_temp_dir("preflight_ndjson_missing_record_field")
        try:
            input_file = temp_path / "dsfe.ndjson"
            output_dir = temp_path / "out"
            input_file.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "member_id": "M-1",
                                "measure_id": "DSF-E",
                                "screening_date": "2025-03-01",
                                "screening_tool": "PHQ-2",
                                "screening_score": "2",
                                "screening_loinc": "44249-1",
                                "bipolar_history": "0",
                                "prior_year_depression_dx": "0",
                                "source_kind": "structured",
                            }
                        ),
                        json.dumps(
                            {
                                "member_id": "M-2",
                                "measure_id": "DSF-E",
                                "screening_date": "2025-03-02",
                                "screening_score": "2",
                                "screening_loinc": "44249-1",
                                "bipolar_history": "0",
                                "prior_year_depression_dx": "0",
                                "source_kind": "structured",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "record 2 is missing required DSF-E fields"):
                run_validation(input_file, output_dir)
        finally:
            cleanup_temp_dir(temp_path)

    def test_run_validation_handles_performance_smoke_dataset(self) -> None:
        temp_path = make_temp_dir("preflight_performance_smoke")
        try:
            input_csv = temp_path / "bulk.csv"
            output_dir = temp_path / "out"
            header = (
                "member_id,measure_id,screening_date,screening_tool,screening_score,screening_loinc,"
                "follow_up_code,follow_up_date,bipolar_history,prior_year_depression_dx,source_kind"
            )
            rows = [
                f"M-{index},DSF-E,2025-04-01,PHQ-2,2,44249-1,,,0,0,structured"
                for index in range(1, 501)
            ]
            input_csv.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
            start = time.perf_counter()
            summary = run_validation(input_csv, output_dir)
            elapsed = time.perf_counter() - start
            self.assertEqual(summary["records_processed"], 500)
            self.assertLess(elapsed, 3.0)
        finally:
            cleanup_temp_dir(temp_path)

    def test_run_validation_writes_audit_event_when_path_provided(self) -> None:
        temp_path = make_temp_dir("preflight_audit")
        try:
            input_csv = temp_path / "dsfe.csv"
            output_dir = temp_path / "out"
            audit_path = temp_path / "audit" / "events.jsonl"
            input_csv.write_text(
                "\n".join(
                    [
                        "member_id,measure_id,screening_date,screening_tool,screening_score,screening_loinc,follow_up_code,follow_up_date,bipolar_history,prior_year_depression_dx,source_kind",
                        "M-100,DSF-E,2025-04-01,PHQ-9,12,44261-6,96127,2025-04-10,0,0,structured",
                    ]
                ),
                encoding="utf-8",
            )
            run_validation(
                input_csv,
                output_dir,
                correlation_id="corr-xyz",
                profile="prod",
                audit_log_path=audit_path,
            )
            audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(audit_lines), 1)
            self.assertIn("corr-xyz", audit_lines[0])
        finally:
            cleanup_temp_dir(temp_path)


if __name__ == "__main__":
    unittest.main()
