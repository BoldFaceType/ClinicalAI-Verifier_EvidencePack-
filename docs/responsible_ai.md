# Responsible AI Notes

This project uses synthetic examples only. Do not commit PHI, payer production files, real member identifiers, or real clinical notes.

## Intended Use

The AI-assisted path is designed for clinical operations and revenue cycle evidence preparation. It helps locate candidate evidence in notes for human review.

## Out of Scope

- autonomous medical decision-making
- autonomous appeal submission
- patient-facing diagnosis or treatment advice
- unsupported summarization of clinical facts

## Guardrails

- AI output must be citation verified before packet inclusion.
- Quotes must appear verbatim in the cited source note.
- Rejected AI evidence remains visible in the audit trail.
- Deterministic mode remains available as an offline fallback.

