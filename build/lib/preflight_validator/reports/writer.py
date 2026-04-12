from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from preflight_validator.rules.engine import RuleResult


def write_reports(
    *,
    input_file: Path,
    output_dir: Path,
    records_processed: int,
    input_format: str,
    findings: list[RuleResult],
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    findings_path = output_dir / "findings.json"
    summary_path = output_dir / "summary.md"
    findings_payload = {
        "validator_version": "0.1.0",
        "ruleset_version": "dsfe-v0.1",
        "input_file": str(input_file),
        "input_format": input_format,
        "records_processed": records_processed,
        "findings": [finding.__dict__ for finding in findings],
    }
    findings_path.write_text(json.dumps(findings_payload, indent=2), encoding="utf-8")
    stage_counts = Counter(finding.stage for finding in findings)
    severity_counts = Counter(finding.severity for finding in findings)
    summary_path.write_text(
        _build_markdown_summary(
            input_file=input_file,
            input_format=input_format,
            records_processed=records_processed,
            findings=findings,
            stage_counts=stage_counts,
            severity_counts=severity_counts,
        ),
        encoding="utf-8",
    )
    return {
        "validator_version": "0.1.0",
        "ruleset_version": "dsfe-v0.1",
        "input_file": str(input_file),
        "input_format": input_format,
        "records_processed": records_processed,
        "finding_count": len(findings),
        "error_count": severity_counts.get("ERROR", 0),
        "warning_count": severity_counts.get("WARN", 0),
        "outputs": {"findings_json": str(findings_path), "summary_markdown": str(summary_path)},
        "stage_counts": dict(stage_counts),
    }


def _build_markdown_summary(
    *,
    input_file: Path,
    input_format: str,
    records_processed: int,
    findings: list[RuleResult],
    stage_counts: Counter[str],
    severity_counts: Counter[str],
) -> str:
    lines = [
        "# DSF-E Pre-flight Validator Summary",
        "",
        f"- Input File: `{input_file}`",
        f"- Input Format: `{input_format}`",
        f"- Records Processed: {records_processed}",
        f"- Findings: {len(findings)}",
        f"- Errors: {severity_counts.get('ERROR', 0)}",
        f"- Warnings: {severity_counts.get('WARN', 0)}",
        "",
        "## Findings by Stage",
    ]
    for stage in sorted(stage_counts):
        lines.append(f"- {stage}: {stage_counts[stage]}")
    lines.extend(["", "## Detailed Findings"])
    if not findings:
        lines.append("- No findings. Input is ready for downstream DSF-E ingestion.")
    else:
        for finding in findings:
            lines.append(
                f"- `{finding.rule_id}` [{finding.severity}] member `{finding.member_id or 'UNKNOWN'}` (row {finding.row_number}, field `{finding.field}`): {finding.message}"
            )
    return "\n".join(lines) + "\n"
