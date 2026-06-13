# ClinicalAI-Verifier â€” Evidence Pack

> **DSF-E Pre-flight Validator + Denial Evidence Packer**
> Clinical AI Engineering Â· v0.3.0 Â· Python 3.11+

[![CI](https://github.com/BoldFaceType/ClinicalAI-Verifier_EvidencePack-/actions/workflows/ci.yml/badge.svg)](https://github.com/BoldFaceType/ClinicalAI-Verifier_EvidencePack-/actions/workflows/ci.yml)

A portfolio-grade toolkit for two adjacent clinical data problems:

1. **Pre-flight Validator** â€” Catches DSF-E (Depression Screening and Follow-up Encounter) data quality issues *before* they reach HEDIS measure processing, surfacing actionable rule findings per member.
2. **Evidence Packer** â€” Parses FHIR ClaimResponse denial payloads and auto-assembles appeal evidence packets from clinical notes, with optional AI-assisted extraction.

---

## Architecture

```
src/
â”œâ”€â”€ cli_common.py                        # Shared Palette, prompt, banner utilities
â”œâ”€â”€ preflight_validator/
â”‚   â”œâ”€â”€ cli.py                           # validate-dsfe CLI entrypoint
â”‚   â”œâ”€â”€ pipeline.py                      # run_validation() orchestrator
â”‚   â”œâ”€â”€ schemas/
â”‚   â”‚   â””â”€â”€ dsfe.py                      # DsfeRecord dataclass + constants
â”‚   â”œâ”€â”€ rules/
â”‚   â”‚   â””â”€â”€ engine.py                    # 20-rule validation engine (6 stages)
â”‚   â””â”€â”€ reports/
â”‚       â””â”€â”€ writer.py                    # findings.json / .csv / per_member.json / summary.md
â””â”€â”€ evidence_packer/
    â”œâ”€â”€ cli.py                           # evidence-packer CLI entrypoint
    â”œâ”€â”€ pipeline.py                      # run_packaging() orchestrator
    â”œâ”€â”€ fetcher/clinical_fetcher.py      # Load .txt / .json clinical notes from directory
    â”œâ”€â”€ handler/
    â”‚   â”œâ”€â”€ denial_handler.py            # Detect denial from ClaimResponse outcome
    â”‚   â””â”€â”€ parser.py                    # Extract DenialDecision from FHIR model
    â”œâ”€â”€ llm/evidence_extractor.py        # Keyword + optional AI evidence extraction
    â”œâ”€â”€ models/fhir_models.py            # FHIR ClaimResponse dataclasses + Pydantic models
    â”œâ”€â”€ output/packet_generator.py       # Generate JSON manifest + PDF appeal packet
    â””â”€â”€ strategy/evidence_mapper.py      # Map denial reason â†’ EvidencePlan
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

## Deployment & Configuration

### Makefile

Common dev/run targets:

```bash
make install   # pip install -e ".[parquet]" + dev deps
make lint      # ruff check src tests
make test      # unittest discover -s tests
make validate  # validate-dsfe against examples/preflight/dsfe_input.csv
make pack      # evidence-packer against examples/evidence/
make clean     # remove caches, build artifacts, and out/
```

### Docker

```bash
docker build -t clinica-ai-engineering .

# validate-dsfe
docker run --rm \
  -v "$(pwd)/examples/preflight:/data/in:ro" \
  -v "$(pwd)/out:/data/out" \
  clinica-ai-engineering \
  validate-dsfe /data/in/dsfe_input.csv /data/out

# evidence-packer
docker run --rm \
  -v "$(pwd)/examples/evidence:/data/in:ro" \
  -v "$(pwd)/out:/data/out" \
  clinica-ai-engineering \
  evidence-packer /data/in/claimresponse_denied.json /data/in/clinical_notes /data/out
```

### docker-compose

```bash
cp .env.example .env   # required â€” compose errors if .env is missing

docker compose run --rm clinica validate-dsfe /data/in/dsfe_input.csv /data/out
docker compose run --rm clinica evidence-packer \
  /data/in/claimresponse_denied.json /data/in/clinical_notes /data/out
```

`docker-compose.yml` mounts `./examples` â†’ `/data/in` (read-only), `./out` â†’ `/data/out`, and `./config.toml` â†’ `/data/config.toml` (auto-detected rule overrides). Point the `./examples` mount at your own data directory for real runs.

### Environment variables (`.env`)

Copy `.env.example` to `.env` and fill in as needed â€” both variables are optional:

| Variable | Used by | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | `evidence-packer --use-ai` | Enables AI-assisted evidence extraction. Without it, heuristic (keyword) mode is used. |
| `CLINICAL_AI_CONFIG` | `validate-dsfe` | Path to a `config.toml` overriding DSF-E rule constants. Default: `./config.toml` in the working directory. |

### Rule configuration (`config.toml`)

`config.toml` at the project root lets you retune DSF-E validation rules â€” approved LOINC codes per tool, positive-screen score thresholds, approved follow-up CPT/HCPCS codes, and the follow-up window in days â€” without editing source. Every section is optional; any key absent from the file falls back to the built-in default (documented inline in the file). Delete `config.toml` entirely to run on defaults.

```toml
[dsfe]
follow_up_codes = ["96127", "G8431", "G8510", "99484"]
follow_up_window_days = 30

[dsfe.approved_loinc_by_tool]
PHQ-2 = ["44249-1"]
PHQ-9 = ["44261-6"]

[dsfe.thresholds]
PHQ-2 = 3
PHQ-9 = 10
```

Requires Python 3.11+ (stdlib `tomllib`). If `config.toml` is absent or unreadable, the validator silently falls back to built-in defaults.

---

## Pre-flight Validator

Validates DSF-E screening input files (CSV, NDJSON, or Parquet) against 20 HEDIS-aligned rules across 6 stages.

### Quick start

```bash
# Quick mode â€” positional args
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
| `findings.csv` | Flat table â€” one row per finding, ready for Excel or BI tools |
| `per_member.json` | Findings grouped by `member_id` for member-level triage |
| `summary.md` | Human-readable summary with counts by stage and severity |

### Rule catalog â€” 20 rules across 6 stages

**Stage 1 Â· File Format**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR1_MISSING_<FIELD>` | ERROR | Required field absent or empty |

**Stage 2 Â· Data Structure**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR2_INVALID_MEASURE_ID` | ERROR | `measure_id` must be `"DSF-E"` |
| `FR2_UNSUPPORTED_SCREENING_TOOL` | ERROR | Tool not in `{PHQ-2, PHQ-9}` |
| `FR2_NON_STRUCTURED_CAPTURE` | ERROR | `source_kind` must be `"structured"` |
| `FR2_NON_NUMERIC_SCREENING_SCORE` | ERROR | Score is not numeric |
| `FR2_NON_DISCRETE_SCREENING_SCORE` | ERROR | Score contains decimal point |
| `FR2_INVALID_SCREENING_DATE_FORMAT` | ERROR | `screening_date` not `YYYY-MM-DD` |
| `FR2_INVALID_MEASURE_YEAR_FORMAT` | WARN | `measure_year` present but not 4-digit `YYYY` |

**Stage 3 Â· Value Sets**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR3_INVALID_LOINC` | ERROR | LOINC not in approved set for tool |
| `FR3_LOINC_TOOL_MISMATCH` | ERROR | LOINC code maps to a different screening tool |

**Stage 4 Â· Threshold Logic**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR4_POSITIVE_SCREEN_MISSING_FOLLOW_UP_CODE` | ERROR | Score â‰¥ threshold but no follow-up code present |

**Stage 5 Â· Follow-up**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR5_INVALID_FOLLOW_UP_CODE` | ERROR | Code not in approved CPT/HCPCS set |
| `FR5_INVALID_FOLLOW_UP_DATE` | ERROR | `follow_up_date` not `YYYY-MM-DD` |
| `FR5_INVALID_SCREENING_DATE` | ERROR | `screening_date` not parseable when follow-up present |
| `FR5_FOLLOW_UP_BEFORE_SCREENING` | ERROR | Follow-up date precedes screening date |
| `FR5_FOLLOW_UP_OUTSIDE_WINDOW` | ERROR | Follow-up > follow-up window after screening (default 30 days, configurable via `config.toml`) |

**Stage 6 Â· Exclusions**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `FR6_INVALID_BIPOLAR_HISTORY_FLAG` | ERROR | `bipolar_history` not boolean-like |
| `FR6_INVALID_PRIOR_YEAR_DEPRESSION_FLAG` | ERROR | `prior_year_depression_dx` not boolean-like |
| `FR6_MEMBER_EXCLUDED_BIPOLAR_HISTORY` | WARN | Member has bipolar history â€” exclusion candidate |
| `FR6_MEMBER_EXCLUDED_PRIOR_DEPRESSION` | WARN | Member has prior-year depression dx â€” exclusion candidate |

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

### Denial â†’ evidence strategy mapping

| Denial keywords | Strategy | Required documents |
|-----------------|----------|--------------------|
| `auth`, `authorization`, `prior auth` | `prior_auth_missing` | auth request, clinical notes, treatment history |
| `necess`, `clinical` | `medical_necessity` | clinical notes, treatment guidelines, outcome measures |
| _(default)_ | `therapy_documentation` | therapy notes, progress reports, discharge summary |

---

## Development

See [Deployment & Configuration](#deployment--configuration) for `make test` / `make lint` / `make validate` / `make pack`. Equivalent direct commands:

```bash
# Run all tests (17 tests across both modules)
PYTHONPATH=src python -m unittest discover -s tests -v

# Lint
ruff check src/ tests/

# CLI smoke test â€” write minimal CSV and validate
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
| **Lint** | `ruff check` â€” E, F, I rules |
| **Test** | `unittest discover` on Python 3.11 and 3.12 |
| **CLI smoke test** | Installs package, writes minimal DSF-E CSV, runs `validate-dsfe`, asserts all 4 output artefacts exist |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

**v0.3.0** â€” Makefile, Dockerfile, docker-compose, `.env.example`, and `config.toml` rule-override layer for deployment and configuration.

**v0.2.0** â€” 3 new rules (`FR2_INVALID_SCREENING_DATE_FORMAT`, `FR2_INVALID_MEASURE_YEAR_FORMAT`, `FR3_LOINC_TOOL_MISMATCH`), `findings.csv` + `per_member.json` outputs, 3-job CI, `instructor` dependency removed.

**v0.1.0** â€” Initial release: 17 rules, DSF-E validator, evidence packer.

---

## Project context

This repo is part of the **Clinical AI Engineering** portfolio â€” production-quality tools addressing real healthcare data problems.

- **DSF-E** is a HEDIS measure tracking depression screening and follow-up care. Malformed input data is the leading cause of measure reporting failures in HEDIS submissions.
- **Evidence Packer** addresses the prior authorization appeal workflow â€” a high-friction, manual process in revenue cycle management that is amenable to structured automation.

Both tools are designed for on-premise deployment with no mandatory cloud dependencies.

---

## Author

**Jeremie Tisby** â€” Clinical AI Engineering Â· 2026