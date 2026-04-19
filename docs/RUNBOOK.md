# Operations Runbook

## Required Runtime Environment
- Python 3.11+
- `CLINICALAI_PROFILE` set to `local`, `staging`, or `prod`
- `CLINICALAI_AUDIT_LOG` configured in non-local environments
- `CLINICALAI_REDACT_LOGS=true` outside local development

## Branch Protection
Configure GitHub branch protection on `main` with required checks:
- `CI / quality`
- Pull request review requirement
- No direct pushes to `main`

## Standard Validation
Run before merge:
1. `python -m ruff check .`
2. `python -m unittest discover -s tests`
3. `python -m build`

## Troubleshooting
- Parse failures: verify JSON/NDJSON validity and schema-required fields.
- No evidence output: verify `ClaimResponse.outcome` is `error` or `partial`.
- Missing notes: confirm note files are `.txt` or `.json` with `text`/`note`.
- Audit gaps: verify `CLINICALAI_AUDIT_LOG` path exists and is writable.

## Rollback
1. Revert to last successful tag.
2. Re-run CI checks and smoke tests.
3. Validate packet and findings contract versions before redeploy.

## Incident Escalation
- Severity 1 (PHI exposure): stop processing, rotate credentials, notify security.
- Severity 2 (incorrect denial classification): disable affected pipeline and hotfix parser rules.
