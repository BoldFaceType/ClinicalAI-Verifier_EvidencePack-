# ClinicalAI-Verifier — Evidence Pack

> **DSF-E Pre-flight Validator + Denial Evidence Packer**
> Clinical AI Engineering · v0.2.0 · Python 3.11+

[![CI](https://github.com/BoldFaceType/ClinicalAI-Verifier_EvidencePack-/actions/workflows/ci.yml/badge.svg)](https://github.com/BoldFaceType/ClinicalAI-Verifier_EvidencePack-/actions/workflows/ci.yml)

A portfolio-grade toolkit for two adjacent clinical data problems:

1. **Pre-flight Validator** — Catches DSF-E (Depression Screening and Follow-up Encounter) data quality issues *before* they reach HEDIS measure processing, surfacing actionable rule findings per member.
2. **Evidence Packer** — Parses FHIR ClaimResponse denial payloads and auto-assembles appeal evidence packets from clinical notes, with optional AI-assisted extraction.

---

## Architecture

```
src/
├── cli_common.py                        # Shared Palette, prompt, banner utilities
├── preflight_validator/
│   ├── cli.py                           # validate-dsfe CLI entrypoint
│   ├── pipeline.py                      # run_validation() orchestrator
│   ├── schemas/
│   │   └── dsfe.py                      # DsfeRecord dataclass + constants
│   ├── rules/
│   │   └── engine.py                    # 20-rule validation engine (6 stages)
│   └── reports/
│       └── writer.py                    # findings.json / .csv / per_member.json / summary.md
└── evidence_packer/
    ├── cli.py                           # evidence-packer CLI entrypoint
    ├── pipeline.py                      # run_packaging() orchestrator
    ├── fetcher/clinical_fetcher.py      # Load .txt / .json clinical notes from directory
    ├── handler/
    │   ├── denial_handler.py            # Detect denial from ClaimResponse outcome
    │   └── parser.py                    # Extract DenialDecision from FHIR model
    ├── llm/evidence_extractor.py        # Keyword + optional AI evidence extraction
    ├── models/fhir_models.py            # FHIR ClaimResponse dataclasses + Pydantic models
    ├── output/packet_generator.py       # Generate JSON manifest + PDF appeal packet
    └── strategy/evidence_mapper.py      # Map denial reason → EvidencePlan
```

Both tools follow **Vertical Slice Architecture**: each module owns its schema, rules, pipeline, reports, and tests end-to-end.

---

## Installation

```bash
# Core install (pydantic only)
pip install -e .

# With optional Parquet support
pip install -e ".[parquet]"
```

Requires Python 3.11+. No LLM API keys needed for standard operation.

---

## Pre-flight Validator

Validates DSF-E screening input files (CSV, NDJSON, or Parquet) against 20 HEDIS-aligned rules across 6 stages.

### Quick start

```bash
# Quick mode — positional args
validate-dsfe input/dsfe_screening.csv out/preflight

# Guided wizard mode
validate-dsfe --wizard

# Disable ANSI color
validate-dsfe input/dsfe_screening.csv out/preflight --no-color
```

### Outputs (written to `output_dir/`)

| File | Description |
|------|-------------|
| `findings.json` | Full structured findings payload with validator metadata |
| `findings.csv` | Flat table — one row per finding, ready for Excel or BI tools |
| `per_member.json` | Findings grouped by `member_id` for member-level triage |
| `summary.md` | Human-readable summary with counts by stage and severity |

### Rule catalog — 20 rules across 6 stages

**Stage 1 · File Format**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR1_MISSING_<FIELD>` | ERROR | Required field absent or empty |

**Stage 2 · Data Structure**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR2_INVALID_MEASURE_ID` | ERROR | `measure_id` must be `"DSF-E"` |
| `FR2_UNSUPPORTED_SCREENING_TOOL` | ERROR | Tool not in `{PHQ-2, PHQ-9}` |
| `FR2_NON_STRUCTURED_CAPTURE` | ERROR | `source_kind` must be `"structured"` |
| `FR2_NON_NUMERIC_SCREENING_SCORE` | ERROR | Score is not numeric |
| `FR2_NON_DISCRETE_SCREENING_SCORE` | ERROR | Score contains decimal point |
| `FR2_INVALID_SCREENING_DATE_FORMAT` | ERROR | `screening_date` not `YYYY-MM-DD` |
| `FR2_INVALID_MEASURE_YEAR_FORMAT` | WARN | `measure_year` present but not 4-digit `YYYY` |

**Stage 3 · Value Sets**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR3_INVALID_LOINC` | ERROR | LOINC not in approved set for tool |
| `FR3_LOINC_TOOL_MISMATCH` | ERROR | LOINC code maps to a different screening tool |

**Stage 4 · Threshold Logic**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR4_POSITIVE_SCREEN_MISSING_FOLLOW_UP_CODE` | ERROR | Score ≥ threshold but no follow-up code present |

**Stage 5 · Follow-up**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR5_INVALID_FOLLOW_UP_CODE` | ERROR | Code not in approved CPT/HCPCS set |
| `FR5_INVALID_FOLLOW_UP_DATE` | ERROR | `follow_up_date` not `YYYY-MM-DD` |
| `FR5_INVALID_SCREENING_DATE` | ERROR | `screening_date` not parseable when follow-up present |
| `FR5_FOLLOW_UP_BEFORE_SCREENING` | ERROR | Follow-up date precedes screening date |
| `FR5_FOLLOW_UP_OUTSIDE_WINDOW` | ERROR | Follow-up > 30 days after screening |

**Stage 6 · Exclusions**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR6_INVALID_BIPOLAR_HISTORY_FLAG` | ERROR | `bipolar_history` not boolean-like |
| `FR6_INVALID_PRIOR_YEAR_DEPRESSION_FLAG` | ERROR | `prior_year_depression_dx` not boolean-like |
| `FR6_MEMBER_EXCLUDED_BIPOLAR_HISTORY` | WARN | Member has bipolar history — exclusion candidate |
| `FR6_MEMBER_EXCLUDED_PRIOR_DEPRESSION` | WARN | Member has prior-year depression dx — exclusion candidate |

### DSF-E input schema

Required fields: `member_id`, `measure_id`, `screening_date`, `screening_tool`, `screening_score`, `screening_loinc`, `bipolar_history`, `prior_year_depression_dx`, `source_kind`

Optional fields: `follow_up_code`, `follow_up_date`, `measure_year`

---

## Evidence Packer

Parses a FHIR R4 `ClaimResponse` denial and assembles an appeal packet from clinical notes.

### Quick start

```bash
# Heuristic mode (no API key required)
evidence-packer claim_response.json notes/ out/appeal

# AI-assisted extraction (requires OPENAI_API_KEY)
evidence-packer claim_response.json notes/ out/appeal --use-ai

# Guided wizard
evidence-packer --wizard
```

### Outputs (written to `output_dir/`)

| File | Description |
|------|-------------|
| `manifest.json` | Structured appeal packet with denial code, strategy, and evidence excerpts |
| `appeal_packet.pdf` | Formatted PDF ready for payer submission |

### Denial → evidence strategy mapping

| Denial keywords | Strategy | Required documents |
|-----------------|----------|--------------------|
| `auth`, `authorization`, `prior auth` | `prior_auth_missing` | auth request, clinical notes, treatment history |
| `necess`, `clinical` | `medical_necessity` | clinical notes, treatment guidelines, outcome measures |
| _(default)_ | `therapy_documentation` | therapy notes, progress reports, discharge summary |

---

## Development

```bash
# Run all tests (17 tests across both modules)
PYTHONPATH=src python -m unittest discover -s tests -v

# Lint
ruff check src/ tests/

# CLI smoke test — write minimal CSV and validate
python - <<'EOF'
import csv, pathlib
fields = ["member_id","measure_id","screening_date","screening_tool",
          "screening_score","screening_loinc","bipolar_history",
          "prior_year_depression_dx","source_kind","follow_up_code",
          "follow_up_date","measure_year"]
row = dict.fromkeys(fields, "")
row.update({"member_id":"SMOKE001","measure_id":"DSF-E",
            "screening_date":"2024-03-15","screening_tool":"PHQ-9",
            "screening_score":"5","screening_loinc":"44261-6",
            "bipolar_history":"false","prior_year_depression_dx":"false",
            "source_kind":"structured"})
p = pathlib.Path("smoke_test.csv")
with p.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerow(row)
EOF
validate-dsfe smoke_test.csv out/smoke
```

### CI pipeline (GitHub Actions)

Three jobs run on every push to `main`:

| Job | What it does |
|-----|-------------|
| **Lint** | `ruff check` — E, F, I rules |
| **Test** | `unittest discover` on Python 3.11 and 3.12 |
| **CLI smoke test** | Installs package, writes minimal DSF-E CSV, runs `validate-dsfe`, asserts all 4 output artefacts exist |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

**v0.2.0** — 3 new rules (`FR2_INVALID_SCREENING_DATE_FORMAT`, `FR2_INVALID_MEASURE_YEAR_FORMAT`, `FR3_LOINC_TOOL_MISMATCH`), `findings.csv` + `per_member.json` outputs, 3-job CI, `instructor` dependency removed.

**v0.1.0** — Initial release: 17 rules, DSF-E validator, evidence packer.

---

## Project context

This repo is part of the **Clinical AI Engineering** portfolio — production-quality tools addressing real healthcare data problems.

- **DSF-E** is a HEDIS measure tracking depression screening and follow-up care. Malformed input data is the leading cause of measure reporting failures in HEDIS submissions.
- **Evidence Packer** addresses the prior authorization appeal workflow — a high-friction, manual process in revenue cycle management that is amenable to structured automation.

Both tools are designed for on-premise deployment with no mandatory cloud dependencies.

---

## Author

**Jeremie Tisby** — Clinical AI Engineering · 2026
