# AI-Assisted Evidence Architecture

The evidence packer is a human-in-the-loop clinical operations assistant for denied payer `ClaimResponse` workflows.

The AI layer has one narrow job: propose exact evidence sentences from synthetic clinical notes. It does not decide whether an appeal should be approved, does not make medical necessity determinations, and does not write unsupported clinical claims.

## Flow

```text
ClaimResponse denial
  -> evidence strategy mapper
  -> clinical notes
  -> optional Azure AI Search retrieval
  -> Azure OpenAI / OpenAI evidence extraction
  -> deterministic citation verification
  -> packet.json + appeal_packet.pdf
```

## Verification Gate

AI-proposed evidence is converted into `CandidateEvidence` and passed through `verify_candidate_evidence`.

Evidence is accepted only when:

- the cited source note exists
- the proposed quote is not empty
- the proposed quote appears verbatim in the source note

Rejected evidence is retained in the audit trail and excluded from the final evidence excerpts.

## Local and Cloud Modes

- `--mode deterministic` uses the existing offline heuristic path.
- `--mode ai-assisted --verify-citations` enables configured AI extraction and records verification audit counts.
- Azure AI Search support is isolated in `evidence_packer.ai.azure_search` and requires the optional `azure` extra.

