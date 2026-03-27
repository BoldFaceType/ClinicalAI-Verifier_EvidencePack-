from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from support import cleanup_temp_dir, make_temp_dir

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_packer.cli import main as evidence_main
from preflight_validator.cli import main as preflight_main


class CliTests(unittest.TestCase):
    def test_preflight_cli_returns_one_for_validation_findings(self) -> None:
        temp_path = make_temp_dir("cli_preflight_findings")
        try:
            input_csv = temp_path / "input.csv"
            output_dir = temp_path / "out"
            input_csv.write_text(
                "member_id,measure_id,screening_date,screening_tool,screening_score,screening_loinc,follow_up_code,follow_up_date,bipolar_history,prior_year_depression_dx,source_kind\n"
                "M-1,DSF-E,2025-01-01,PHQ-2,4,99999-9,,,0,0,free_text\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            original_argv = sys.argv[:]
            try:
                sys.argv = ["validate_dsfe", str(input_csv), str(output_dir)]
                with redirect_stdout(stdout):
                    exit_code = preflight_main()
            finally:
                sys.argv = original_argv
            self.assertEqual(exit_code, 1)
            self.assertTrue((output_dir / "findings.json").exists())
            self.assertIn("Validation found issues", stdout.getvalue())
        finally:
            cleanup_temp_dir(temp_path)

    def test_preflight_cli_returns_two_for_fatal_input_error(self) -> None:
        temp_path = make_temp_dir("cli_preflight_fatal")
        try:
            missing_file = temp_path / "missing.csv"
            output_dir = temp_path / "out"
            stdout = io.StringIO()
            original_argv = sys.argv[:]
            try:
                sys.argv = ["validate_dsfe", str(missing_file), str(output_dir)]
                with redirect_stdout(stdout):
                    exit_code = preflight_main()
            finally:
                sys.argv = original_argv
            self.assertEqual(exit_code, 2)
            self.assertIn("fatal_error", stdout.getvalue())
        finally:
            cleanup_temp_dir(temp_path)

    def test_evidence_cli_returns_zero_for_generated_packet(self) -> None:
        temp_path = make_temp_dir("cli_evidence_success")
        try:
            claim_response_json = temp_path / "claimresponse.json"
            notes_dir = temp_path / "notes"
            output_dir = temp_path / "out"
            notes_dir.mkdir()
            claim_response_json.write_text(
                json.dumps(
                    {
                        "resourceType": "ClaimResponse",
                        "outcome": "error",
                        "disposition": "Authorization missing",
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
            (notes_dir / "note.txt").write_text(
                "Authorization was approved and documented in the chart.",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            original_argv = sys.argv[:]
            try:
                sys.argv = [
                    "evidence-packer",
                    str(claim_response_json),
                    str(notes_dir),
                    str(output_dir),
                ]
                with redirect_stdout(stdout):
                    exit_code = evidence_main()
            finally:
                sys.argv = original_argv
            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "appeal_packet.pdf").exists())
            self.assertIn("Appeal packet generated", stdout.getvalue())
        finally:
            cleanup_temp_dir(temp_path)

    def test_evidence_cli_returns_one_for_no_action(self) -> None:
        temp_path = make_temp_dir("cli_evidence_no_action")
        try:
            claim_response_json = temp_path / "claimresponse.json"
            notes_dir = temp_path / "notes"
            output_dir = temp_path / "out"
            notes_dir.mkdir()
            claim_response_json.write_text(
                json.dumps(
                    {
                        "resourceType": "ClaimResponse",
                        "outcome": "complete",
                        "disposition": "Paid",
                        "item": [],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            original_argv = sys.argv[:]
            try:
                sys.argv = [
                    "evidence-packer",
                    str(claim_response_json),
                    str(notes_dir),
                    str(output_dir),
                ]
                with redirect_stdout(stdout):
                    exit_code = evidence_main()
            finally:
                sys.argv = original_argv
            self.assertEqual(exit_code, 1)
            self.assertIn("no_action", stdout.getvalue())
        finally:
            cleanup_temp_dir(temp_path)

    def test_preflight_cli_wizard_path_runs_with_hotkeys(self) -> None:
        temp_path = make_temp_dir("cli_preflight_wizard")
        try:
            input_csv = temp_path / "input.csv"
            output_dir = temp_path / "out"
            input_csv.write_text(
                "member_id,measure_id,screening_date,screening_tool,screening_score,screening_loinc,bipolar_history,prior_year_depression_dx,source_kind\n"
                "M-1,DSF-E,2025-01-01,PHQ-2,2,44249-1,0,0,structured\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch("builtins.input", side_effect=[str(input_csv), str(output_dir), "r", "y"]):
                with redirect_stdout(stdout):
                    exit_code = preflight_main(["--wizard", "--no-color"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Validation passed", stdout.getvalue())
        finally:
            cleanup_temp_dir(temp_path)

    def test_evidence_cli_wizard_allows_heuristic_hotkey_path(self) -> None:
        temp_path = make_temp_dir("cli_evidence_wizard")
        try:
            claim_response_json = temp_path / "claimresponse.json"
            notes_dir = temp_path / "notes"
            output_dir = temp_path / "out"
            notes_dir.mkdir()
            claim_response_json.write_text(
                json.dumps(
                    {
                        "resourceType": "ClaimResponse",
                        "outcome": "error",
                        "disposition": "Authorization missing",
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
            (notes_dir / "note.txt").write_text(
                "Authorization was approved and documented in the chart.",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch(
                "builtins.input",
                side_effect=[
                    str(claim_response_json),
                    str(notes_dir),
                    str(output_dir),
                    "h",
                    "r",
                    "y",
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = evidence_main(["--wizard", "--no-color"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Appeal packet generated", stdout.getvalue())
        finally:
            cleanup_temp_dir(temp_path)


if __name__ == "__main__":
    unittest.main()
