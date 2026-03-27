from __future__ import annotations

import json
from pathlib import Path

from evidence_packer.fetcher.clinical_fetcher import load_clinical_notes
from evidence_packer.handler.denial_handler import should_continue
from evidence_packer.handler.parser import parse_denial_reason
from evidence_packer.llm.evidence_extractor import extract_supporting_evidence
from evidence_packer.models.fhir_models import parse_claim_response
from evidence_packer.output.packet_generator import generate_appeal_packet
from evidence_packer.strategy.evidence_mapper import resolve_evidence_strategy

PackagingSummary = dict[str, object]


def run_packaging(
    claim_response_json: Path,
    notes_dir: Path,
    output_dir: Path,
    *,
    use_ai: bool = False,
) -> PackagingSummary:
    if not claim_response_json.exists():
        raise ValueError(f"ClaimResponse file does not exist: {claim_response_json}")
    if not claim_response_json.is_file():
        raise ValueError(
            f"ClaimResponse path must point to a JSON file, not a directory: {claim_response_json}"
        )
    if claim_response_json.suffix.lower() != ".json":
        raise ValueError(
            f"ClaimResponse input must be a .json file. Received: {claim_response_json.name}"
        )

    try:
        payload = json.loads(claim_response_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"ClaimResponse JSON could not be parsed: {exc.msg} at line {exc.lineno}, column {exc.colno}."
        ) from exc

    model = parse_claim_response(payload)

    if model.resource_type != "ClaimResponse":
        raise ValueError(
            "Input must be a FHIR ClaimResponse resource. If you passed a Bundle, extract the ClaimResponse first."
        )

    if not should_continue(model):
        summary: PackagingSummary = {
            "claim_response_file": str(claim_response_json),
            "status": "no_action",
            "message": "ClaimResponse outcome is not denied or partially denied.",
            "output_generated": False,
            "ai_assisted": use_ai,
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    denial = parse_denial_reason(model)
    evidence_plan = resolve_evidence_strategy(denial)
    notes = load_clinical_notes(notes_dir)
    excerpts = extract_supporting_evidence(
        notes,
        evidence_plan,
        denial.denial_text,
        use_ai=use_ai,
    )
    manifest = generate_appeal_packet(
        output_dir=output_dir,
        claim_response_path=claim_response_json,
        outcome=denial.outcome,
        denial_code=denial.denial_code,
        denial_text=denial.denial_text,
        evidence_plan=evidence_plan,
        excerpts=excerpts,
    )

    summary: PackagingSummary = {
        "claim_response_file": str(claim_response_json),
        "status": "appeal_packet_generated",
        "outcome": denial.outcome,
        "denial_code": denial.denial_code,
        "strategy_category": evidence_plan.category,
        "required_documents": evidence_plan.required_documents,
        "excerpt_count": len(excerpts),
        "ai_assisted": use_ai,
        "output_generated": True,
        "outputs": {
            "packet_pdf": manifest["packet_pdf"],
            "packet_json": str(output_dir / "packet.json"),
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
