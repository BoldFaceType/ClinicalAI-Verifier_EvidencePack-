# Evidence Strategy Catalog

This catalog documents the v0.1 denial-to-evidence mapping used by `evidence_packer`.

## Intake Contract

Primary input is a FHIR `ClaimResponse` JSON document.

The workflow only continues when `ClaimResponse.outcome` is one of:

- `error`
- `partial`

All other outcomes return `status = no_action` and do not generate an appeal packet.

## Denial Parsing

The denial parser reads:

- `ClaimResponse.disposition`
- `ClaimResponse.item[].adjudication[].reason`

Normalized output fields:

- `denial_code`
- `denial_text`
- `outcome`
- `disposition`

## Strategy Categories

### `prior_auth_missing`

Matched when denial code or denial text contains authorization-oriented terms such as:

- `AUTH`
- `authorization`
- `prior auth`

Required documents:

- `authorization`
- `denial_letter`
- `claim_summary`

Search terms used by the v0.1 extractor:

- `authorization`
- `approved`
- `prior auth`
- `referral`

### `medical_necessity`

Matched when denial text contains medical-necessity or clinical-documentation terms such as:

- `necess`
- `clinical`

Required documents:

- `clinical_notes`
- `denial_letter`
- `claim_summary`

Search terms:

- `medical necessity`
- `symptoms`
- `assessment`
- `plan`

### `conservative_therapy_missing`

Fallback strategy for v0.1 when denial text does not match the prior categories.

Required documents:

- `pt_notes`
- `pcp_notes`
- `medication_history`

Search terms:

- `physical therapy`
- `conservative`
- `medication`
- `PCP`

## Clinical Evidence Fetching

v0.1 reads only local note files from a directory:

- `.txt`
- `.json` with a top-level `text` or `note` field

This is intentionally a stub for future FHIR `DocumentReference` or `ClinicalImpression` integration.

## Evidence Extraction

The v0.1 extractor is deterministic and heuristic-based.

For each note it:

- splits text into sentence-like segments
- scores segments by matching strategy search terms and denial-text terms
- returns the best excerpt per note with a numeric confidence

This keeps runtime behavior auditable while reserving true LLM orchestration for a later slice.

## Output Contract

Generated outputs:

- `summary.json`
- `packet.json`
- `appeal_packet.pdf`

`packet.json` includes:

- denial metadata
- strategy category
- required documents
- extracted evidence excerpts
- `appeal_ready` boolean
