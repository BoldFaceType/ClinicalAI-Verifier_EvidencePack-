# Revised To-Do List

## Pre-flight Validator

Source brief: `Pre-flight Validator (dsf-e) – Repo Ready Package V0.1.txt`

1. Add a proper schema layer for DSF-E input records, starting with `pydantic` models and a loader abstraction that can support CSV first and Parquet / NDJSON next.
2. Expand validation beyond basic CSV hygiene into the rule set called out in the brief: LOINC presence, numeric structured results, value set checks, threshold logic, follow-up window checks, and exclusion detection.
3. Keep the rule engine pure and deterministic, with rule-level error codes and stable outputs for the same input.
4. Add JSON findings output and a human-readable Markdown summary that can be used in CI or audit prep.
5. Add a CLI entry point with clear exit codes so the validator can be used as a local gate or a pipeline step.
6. Add sample DSF-E inputs and focused tests for each rule category before broadening the supported file formats.
7. Defer multi-measure support until the DSF-E slice is stable and the current rule set is well-covered.

## Evidence Packer

Source brief: `Evidence Packer (rcm Denial Management) — Repo Ready.txt`

1. Re-scope the current packer from claim/attachment grouping into a FHIR `ClaimResponse` denial workflow.
2. Add FHIR models for denied or partially denied responses and a parser that extracts denial code, denial text, and outcome.
3. Implement the evidence strategy resolver as a rule-based mapper from denial category to evidence query plan.
4. Stub the clinical notes fetcher against local JSON or text fixtures first, then leave a clean interface for future FHIR `DocumentReference` or `ClinicalImpression` support.
5. Add an evidence extractor layer that can highlight supporting sentences and attach confidence scores, even if the first version uses a local stub instead of a live LLM.
6. Build the appeal packet generator around the brief’s primary output, which is a PDF, with ZIP as an optional future format.
7. Add sample denied `ClaimResponse` JSON, sample clinical notes, and tests for denial detection, strategy mapping, and packet generation.
8. Keep the v1 narrow: no EHR auth, no X12 parsing, no payer submission, and no UI.

