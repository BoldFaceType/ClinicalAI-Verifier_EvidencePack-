# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] â€” 2026-04-19

### Added

**Pre-flight Validator**
- `FR2_INVALID_SCREENING_DATE_FORMAT` â€” ERROR rule: `screening_date` must be `YYYY-MM-DD`
- `FR2_INVALID_MEASURE_YEAR_FORMAT` â€” WARN rule: `measure_year`, when present, must be 4-digit `YYYY`
- `FR3_LOINC_TOOL_MISMATCH` â€” ERROR rule: LOINC code present but maps to a different screening tool than declared
- `findings.csv` output â€” flat table, one row per finding, ready for Excel or BI tools
- `per_member.json` output â€” findings grouped by `member_id` for member-level triage
- `measure_year` optional field added to `DsfeRecord` dataclass and `DsfeRowModel` Pydantic model
- `LOINC_TO_TOOL` reverse map derived from `APPROVED_LOINC_BY_TOOL` in `schemas/dsfe.py`
- `MEASURE_ID` and `VALID_SOURCE_KINDS` constants in `schemas/dsfe.py`
- Validator version (`0.2.0`) and ruleset version (`dsfe-v0.2`) embedded in `findings.json` payload

**CI / Packaging**
- 3-job GitHub Actions pipeline: **Lint** (ruff), **Test** (Python 3.11 + 3.12 matrix), **CLI smoke test**
- Smoke test asserts all 4 output artefacts exist: `findings.json`, `findings.csv`, `per_member.json`, `summary.md`

### Changed

- `pyproject.toml`: version bumped to `0.2.0`, author updated to Jeremie Tisby
- `pyproject.toml`: `instructor` removed from core `dependencies` (optional â€” loaded lazily at runtime only when `--use-ai` flag is set and `OPENAI_API_KEY` is present)
- `write_reports()` return dict updated: `outputs` key now includes all 4 output file paths

### Fixed

- `evidence_extractor.py`: `import instructor` and `from openai import OpenAI` moved inside `_build_instructor_client()` with `try/except ImportError` guard â€” prevents `ModuleNotFoundError` when `instructor` is not installed

---

## [0.1.0] â€” 2026-04-01

### Added

**Pre-flight Validator** (`validate-dsfe` CLI)
- 17-rule DSF-E validation engine across 6 stages: File Format, Data Structure, Value Sets, Threshold Logic, Follow-up, Exclusions
- Input format support: CSV, NDJSON, Parquet (Parquet requires optional `pyarrow` extra)
- `findings.json` output â€” full structured findings payload with validator metadata
- `summary.md` output â€” human-readable summary with counts by stage and severity
- Guided `--wizard` mode for interactive input
- `--no-color` flag for ANSI-free output
- LOINC value set validation for PHQ-2 and PHQ-9 screening tools
- Follow-up window enforcement (â‰¤ 30 days after screening date)
- Exclusion candidate flagging for bipolar history and prior-year depression diagnosis

**Evidence Packer** (`evidence-packer` CLI)
- FHIR R4 `ClaimResponse` denial parsing via Pydantic models
- Denial reason â†’ evidence strategy mapping (prior auth, medical necessity, therapy documentation)
- Clinical note ingestion from `.txt` and `.json` files in a directory
- Keyword-based evidence extraction (heuristic mode, no API key required)
- Optional AI-assisted evidence extraction via `instructor` + OpenAI (`--use-ai` flag, requires `OPENAI_API_KEY`)
- `manifest.json` output â€” structured appeal packet with denial code, strategy, and evidence excerpts
- `appeal_packet.pdf` output â€” formatted PDF ready for payer submission
- Guided `--wizard` mode

**Shared**
- `cli_common.py` â€” shared Palette, prompt, and banner utilities
- Vertical Slice Architecture: each module owns schema, rules, pipeline, reports, and tests end-to-end
- 17 unit tests across both modules (`unittest discover`)
- `pyproject.toml` with `setuptools` build backend and `ruff` linting config

---

[0.2.0]: https://github.com/BoldFaceType/ClinicalAI-Verifier_EvidencePack-/releases/tag/v0.2.0
[0.1.0]: https://github.com/BoldFaceType/ClinicalAI-Verifier_EvidencePack-/releases/tag/v0.1.0