# Security and PHI Handling Policy

## Scope
- Applies to `preflight_validator` and `evidence_packer`.
- Treat all member, claim, and note data as PHI by default.

## Required Controls
- Encrypt PHI at rest using managed KMS keys.
- Encrypt PHI in transit with TLS 1.2+.
- Never log raw note text, claim payloads, member identifiers, or full denial documents.
- Enable log redaction (`CLINICALAI_REDACT_LOGS=true`) in all non-local environments.
- Use short-lived credentials from a secret manager; do not store secrets in code or CI variables unencrypted.
- Use least-privilege service roles with read access only to required data paths.

## Retention and Deletion
- Keep generated packet outputs only for approved operational retention windows.
- Configure automatic deletion for audit and packet artifacts based on organizational policy.
- If a request is cancelled or invalid, avoid writing intermediate PHI artifacts.

## Audit Trail Requirements
- Capture correlation ID, profile, event name, denial code, strategy category, and output status.
- Store audit logs in append-only storage with restricted write permissions.
- Keep audit records immutable for compliance reviews.

## Incident Response
- Follow runbook escalation in `docs/RUNBOOK.md`.
- Rotate credentials immediately for suspected compromise.
- Preserve forensic logs and audit events for review.
