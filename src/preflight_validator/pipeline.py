from __future__ import annotations

import csv
import json
from pathlib import Path

from preflight_validator.reports.writer import write_reports
from preflight_validator.rules.engine import run_rules
from preflight_validator.schemas.dsfe import REQUIRED_FIELDS, DsfeRecord
from runtime_support import append_audit_event

ValidationSummary = dict[str, object]


def run_validation(
    input_file: Path,
    output_dir: Path,
    *,
    correlation_id: str | None = None,
    profile: str = "local",
    audit_log_path: Path | None = None,
) -> ValidationSummary:
    if not input_file.exists():
        raise ValueError(f"Input file does not exist: {input_file}")
    if not input_file.is_file():
        raise ValueError(f"Input path must point to a file, not a directory: {input_file}")
    input_format = _detect_input_format(input_file)
    rows = _load_rows(input_file, input_format)
    records = [
        DsfeRecord.from_mapping(row, input_format=input_format, row_number=index)
        for index, row in enumerate(rows, start=2)
    ]
    findings = run_rules(records)
    summary = write_reports(
        input_file=input_file,
        output_dir=output_dir,
        records_processed=len(records),
        input_format=input_format,
        findings=findings,
        correlation_id=correlation_id or "",
        profile=profile,
    )
    append_audit_event(
        audit_log_path,
        {
            "event": "preflight.validation.completed",
            "correlation_id": correlation_id or "",
            "profile": profile,
            "records_processed": len(records),
            "error_count": summary["error_count"],
            "warning_count": summary["warning_count"],
            "input_file": str(input_file),
        },
    )
    return summary


def _detect_input_format(input_file: Path) -> str:
    suffix = input_file.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".ndjson":
        return "ndjson"
    if suffix == ".parquet":
        return "parquet"
    raise ValueError(
        f"Unsupported input format '{input_file.suffix}'. Supported formats are: .csv, .ndjson, and .parquet."
    )


def _load_rows(input_file: Path, input_format: str) -> list[dict[str, object]]:
    if input_format == "csv":
        return _load_csv_rows(input_file)
    if input_format == "ndjson":
        return _load_ndjson_rows(input_file)
    return _load_parquet_rows(input_file)


def _load_csv_rows(input_file: Path) -> list[dict[str, object]]:
    with input_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(
                "The CSV file is missing a header row. The first row must name the DSF-E fields."
            )
        missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
        if missing:
            raise ValueError(
                "The CSV file is missing required DSF-E columns: " + ", ".join(missing) + "."
            )
        return [
            row for row in reader if row and any((value or "").strip() for value in row.values())
        ]


def _load_ndjson_rows(input_file: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with input_file.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"NDJSON parsing failed on line {line_number}: {exc.msg}. "
                    "Each line must be a valid JSON object."
                ) from exc
            if not isinstance(payload, dict):
                raise ValueError(
                    f"NDJSON line {line_number} is not a JSON object. Each line must be an object with DSF-E fields."
                )
            rows.append(payload)
    _validate_required_fields(rows, input_format="NDJSON")
    return rows


def _load_parquet_rows(input_file: Path) -> list[dict[str, object]]:
    try:
        import pyarrow.parquet as pq  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ValueError(
            "Parquet input requires the optional 'parquet' dependency. Install pyarrow before using .parquet files."
        ) from exc
    table = pq.read_table(input_file)
    rows = table.to_pylist()
    _validate_required_fields(rows, input_format="Parquet")
    return rows


def _validate_required_fields(rows: list[dict[str, object]], *, input_format: str) -> None:
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(
                f"{input_format} record {index} is not an object with DSF-E fields."
            )
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            raise ValueError(
                f"{input_format} record {index} is missing required DSF-E fields: "
                + ", ".join(missing)
                + "."
            )
