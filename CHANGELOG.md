# CHANGELOG

## [0.2.0] - 2026-04-01

### Added
- FR2_INVALID_SCREENING_DATE_FORMAT (ERROR) - screening_date must be YYYY-MM-DD
- FR2_INVALID_MEASURE_YEAR_FORMAT (WARN) - measure_year must be 4-digit YYYY
- FR3_LOINC_TOOL_MISMATCH (ERROR) - LOINC code belongs to wrong screening tool
- findings.csv output artefact
- per_member.json output artefact
- Per-member summary table in summary.md
- GitHub Actions CI workflow (lint + test matrix 3.11/3.12 + CLI smoke test)
- 88 tests (50 preflight_validator + 38 evidence_packer)

### Changed
- version 0.1.0 -> 0.2.0
- instructor removed from required deps (optional AI path only)
- FOLLOW_UP_CODES, BOOLEAN_TRUE, BOOLEAN_FALSE -> frozenset
- Author: Jeremie Tisby

### Fixed
- FR5_INVALID_SCREENING_DATE could silently skip when screening_date had
  non-ISO format and no follow-up was present. Now caught in Stage 2.

## [0.1.0] - 2025-01-01 (initial release)
