# Clinica AI Engineering

This workspace now contains v1 Python implementations for both repo-ready concepts:

- `preflight_validator`: a deterministic DSF-E pre-flight validator that checks schema, structure, value sets, thresholds, follow-up windows, and exclusions before HEDIS ingestion
- `evidence_packer`: a denial-driven appeal packet generator that ingests payer `ClaimResponse` JSON, loads local clinical notes, extracts supporting excerpts, and emits a PDF packet

Both tools are intentionally narrow and mostly standard-library based so they can run in constrained environments and remain easy to audit. The code is prepared to use `pydantic` when available, and the packaging metadata now declares it directly.

## Project Layout

```text
src/
  preflight_validator/
  evidence_packer/
tests/
examples/
docs/
```

## Pre-flight Validator

Purpose: catch DSF-E quality failures before downstream HEDIS ingestion.

Supported inputs:

- `CSV`
- `NDJSON`
- `Parquet` when the optional `parquet` extra is installed

Required fields:

- `member_id`
- `measure_id`
- `screening_date`
- `screening_tool`
- `screening_score`
- `screening_loinc`
- `bipolar_history`
- `prior_year_depression_dx`
- `source_kind`

Optional follow-up fields:

- `follow_up_code`
- `follow_up_date`

Output files:

- `findings.json`
- `summary.md`

Reference:

- [DSF-E Rule Catalog](C:\Dev\projects\Clinica AI Engineering\docs\rule_catalog.md)

Example:

```powershell
validate-dsfe .\examples\preflight\dsfe_input.csv .\out\preflight
```

## Evidence Packer

Purpose: generate an appeal packet from a denied or partially denied payer `ClaimResponse`.

Inputs:

- `ClaimResponse` JSON
- local directory of `.txt` or `.json` clinical notes

Output files:

- `summary.json`
- `packet.json`
- `appeal_packet.pdf`

Reference:

- [Evidence Strategy Catalog](C:\Dev\projects\Clinica AI Engineering\docs\evidence_strategy_catalog.md)

Example:

```powershell
evidence-packer .\examples\evidence\claimresponse_denied.json .\examples\evidence\clinical_notes .\out\evidence
```

## Installation Notes

Base dependency:

```powershell
pip install .
```

With optional Parquet support:

```powershell
pip install .[parquet]
```

## Running Tests

```powershell
python -m unittest discover -s tests
```

The tests prepend `src` to `sys.path`, so they can run without installing the package first.
The current shell does not expose Python on `PATH`, so test execution may require activating your local interpreter first.
