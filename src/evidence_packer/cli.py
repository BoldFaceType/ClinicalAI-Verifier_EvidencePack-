from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from cli_common import (
    Palette,
    build_error_payload,
    confirm,
    print_banner,
    print_kv,
    prompt_choice,
    prompt_text,
)
from evidence_packer.pipeline import run_packaging
from runtime_support import classify_error, emit_structured_log, load_runtime_settings

ParserConfig = dict[str, Path | bool]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evidence-packer",
        description=(
            "Generate an appeal packet from a denied FHIR ClaimResponse and a set of local clinical notes.\n\n"
            "This CLI supports two usage styles:\n"
            "  1. Guided mode for users who want prompts, review, and hotkeys\n"
            "  2. Quick mode for veteran users who want to pass paths directly"
        ),
        epilog=(
            "Examples:\n"
            "  Guided walkthrough:\n"
            "    evidence-packer --wizard\n\n"
            "  Quick path with heuristic extraction:\n"
            "    evidence-packer .\\samples\\claimresponse_denied.json .\\samples\\clinical_notes .\\out\\evidence\n\n"
            "  AI-assisted extraction with Instructor:\n"
            "    evidence-packer claim.json notes out --use-ai\n\n"
            "Troubleshooting:\n"
            "  - If the file is not a ClaimResponse, extract the ClaimResponse resource before running.\n"
            "  - If no notes are found, add .txt notes or JSON notes with a 'text' or 'note' field.\n"
            "  - If --use-ai is enabled, set OPENAI_API_KEY if you expect AI-assisted extraction.\n"
            "  - If you are unsure about paths or mode, rerun with --wizard."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "claim_response_json",
        nargs="?",
        type=Path,
        help="Path to the denied ClaimResponse JSON file.",
    )
    parser.add_argument(
        "notes_dir",
        nargs="?",
        type=Path,
        help="Directory containing .txt notes or note-like JSON files.",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        help="Directory where the packet JSON, summary, and PDF placeholder will be written.",
    )
    parser.add_argument(
        "-w",
        "--wizard",
        action="store_true",
        help="Launch a guided, step-by-step packet-building flow with hotkeys.",
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        help="Use Instructor + OpenAI for structured excerpt extraction when OPENAI_API_KEY is set.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors and terminal highlighting.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Runtime profile (defaults to CLINICALAI_PROFILE or local).",
    )
    parser.add_argument(
        "--correlation-id",
        default=None,
        help="Correlation ID for logs and audit records.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    palette = Palette(enabled=not args.no_color)
    settings = load_runtime_settings(
        tool="evidence_packer",
        profile=args.profile,
        correlation_id=args.correlation_id,
    )
    config = _collect_cli_config(
        wizard=args.wizard or not (args.claim_response_json and args.notes_dir and args.output_dir),
        claim_response_json=args.claim_response_json,
        notes_dir=args.notes_dir,
        output_dir=args.output_dir,
        use_ai=args.use_ai,
        palette=palette,
    )
    if config is None:
        print(
            json.dumps(
                {
                    "status": "cancelled",
                    "message": "Evidence packing cancelled by user.",
                    "correlation_id": settings.correlation_id,
                },
                indent=2,
            )
        )
        return 2

    emit_structured_log(settings, level="info", event="evidence.packing.start", payload=config)
    try:
        summary = run_packaging(
            config["claim_response_json"],
            config["notes_dir"],
            config["output_dir"],
            use_ai=bool(config["use_ai"]),
            correlation_id=settings.correlation_id,
            profile=settings.profile,
            audit_log_path=settings.audit_log_path,
        )
    except (OSError, ValueError) as exc:
        app_error = classify_error("evidence", exc)
        payload = build_error_payload(
            tool="evidence_packer",
            exc=app_error,
            error_code=app_error.code,
            correlation_id=settings.correlation_id,
            inputs=config,
            hints=[
                "Confirm that the ClaimResponse path points to a readable JSON file.",
                "Make sure the JSON payload is a FHIR ClaimResponse resource, not a Bundle or another resource type.",
                "Check that the notes directory exists and contains note text the packer can scan.",
                "If you enabled --use-ai, verify that OPENAI_API_KEY is set if you expect AI-assisted extraction.",
                "Re-run with --wizard if you want the CLI to guide you through the inputs again.",
            ],
        )
        print(palette.error("Evidence packet generation could not start."))
        print(palette.warning(str(app_error)))
        print(json.dumps(payload, indent=2))
        emit_structured_log(
            settings,
            level="error",
            event="evidence.packing.failed",
            payload={"error_code": app_error.code, "message": str(app_error)},
        )
        return 2
    _print_human_summary(summary, palette)
    emit_structured_log(
        settings,
        level="info",
        event="evidence.packing.completed",
        payload={
            "status": summary.get("status"),
            "output_generated": summary.get("output_generated"),
            "excerpt_count": summary.get("excerpt_count"),
        },
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("output_generated") else 1


def _collect_cli_config(
    *,
    wizard: bool,
    claim_response_json: Path | None,
    notes_dir: Path | None,
    output_dir: Path | None,
    use_ai: bool,
    palette: Palette,
) -> ParserConfig | None:
    if not wizard:
        if claim_response_json is None or notes_dir is None or output_dir is None:
            raise ValueError(
                "claim_response_json, notes_dir, and output_dir are required in quick mode."
            )
        return {
            "claim_response_json": claim_response_json,
            "notes_dir": notes_dir,
            "output_dir": output_dir,
            "use_ai": use_ai,
        }

    print_banner(
        palette,
        "Evidence Packer",
        "Guided mode helps collect the denial file, notes, and output location with single-key actions.",
    )
    chosen_claim = Path(
        prompt_text("ClaimResponse JSON path", default=str(claim_response_json or ""))
    )
    chosen_notes = Path(
        prompt_text("Clinical notes directory", default=str(notes_dir or "samples\\clinical_notes"))
    )
    chosen_output = Path(
        prompt_text("Output directory", default=str(output_dir or "out\\evidence"))
    )
    ai_choice = prompt_choice(
        "Extraction mode.",
        {"h": "heuristic (offline-safe)", "a": "ai-assisted with Instructor"},
        default="a" if use_ai else "h",
    )
    print()
    print_kv(palette, "ClaimResponse", str(chosen_claim))
    print_kv(palette, "Notes", str(chosen_notes))
    print_kv(palette, "Output", str(chosen_output))
    print_kv(palette, "Mode", "AI-assisted" if ai_choice == "a" else "Heuristic")
    print()
    action = prompt_choice(
        "Choose your next step.",
        {"r": "run packet build", "e": "edit values", "q": "quit"},
        default="r",
    )
    if action == "q":
        return None
    if action == "e":
        return _collect_cli_config(
            wizard=True,
            claim_response_json=chosen_claim,
            notes_dir=chosen_notes,
            output_dir=chosen_output,
            use_ai=ai_choice == "a",
            palette=palette,
        )
    if not confirm("Generate the packet now?", default=True):
        return None
    return {
        "claim_response_json": chosen_claim,
        "notes_dir": chosen_notes,
        "output_dir": chosen_output,
        "use_ai": ai_choice == "a",
    }


def _print_human_summary(summary: dict[str, object], palette: Palette) -> None:
    print()
    if summary.get("output_generated"):
        print(palette.success("Appeal packet generated"))
    elif summary.get("status") == "no_action":
        print(palette.warning("No denial action required"))
    else:
        print(palette.error("Evidence packing ended with an unexpected state"))
    print_kv(palette, "Status", str(summary.get("status", "")))
    print_kv(palette, "Denial Code", str(summary.get("denial_code", "n/a")))
    print_kv(palette, "Strategy", str(summary.get("strategy_category", "n/a")))
    print_kv(palette, "AI Assisted", str(summary.get("ai_assisted", False)))
    outputs = summary.get("outputs", {})
    if isinstance(outputs, dict):
        for label, path in outputs.items():
            print_kv(palette, label, str(path))
    print()


if __name__ == "__main__":
    raise SystemExit(main())
