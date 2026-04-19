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
from preflight_validator.pipeline import run_validation

ParserConfig = dict[str, Path]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_dsfe",
        description=(
            "Validate DSF-E screening input before it reaches downstream HEDIS processing.\n\n"
            "This CLI supports two usage styles:\n"
            "  1. Guided mode for new or occasional users\n"
            "  2. Quick mode for experienced users who already know their file paths"
        ),
        epilog=(
            "Examples:\n"
            "  Guided walkthrough:\n"
            "    validate_dsfe --wizard\n\n"
            "  Quick path for experienced users:\n"
            "    validate_dsfe .\\input\\dsfe.csv .\\out\\preflight\n\n"
            "  Disable ANSI color if your terminal does not render colors cleanly:\n"
            "    validate_dsfe .\\input\\dsfe.ndjson .\\out\\preflight --no-color\n\n"
            "Troubleshooting:\n"
            "  - If you see 'Input file does not exist', double-check the path and filename.\n"
            "  - If you see 'missing required columns/fields', compare your file to the DSF-E schema.\n"
            "  - If you are using Parquet, install the optional parquet dependency first.\n"
            "  - If you want the tool to guide you through the inputs again, rerun with --wizard."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="Path to the DSF-E input file (.csv, .ndjson, or .parquet).",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        help="Directory where findings and summaries will be written.",
    )
    parser.add_argument(
        "-w",
        "--wizard",
        action="store_true",
        help="Launch a guided, step-by-step flow with hotkeys for review and confirmation.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors and highlighting in terminal output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    palette = Palette(enabled=not args.no_color)
    config = _collect_cli_config(
        wizard=args.wizard or not (args.input_file and args.output_dir),
        input_file=args.input_file,
        output_dir=args.output_dir,
        palette=palette,
    )
    if config is None:
        print(
            json.dumps(
                {"status": "cancelled", "message": "Validation cancelled by user."}, indent=2
            )
        )
        return 2

    try:
        summary = run_validation(config["input_file"], config["output_dir"])
    except (OSError, ValueError) as exc:
        payload = build_error_payload(
            tool="preflight_validator",
            exc=exc,
            inputs=config,
            hints=[
                "Confirm that the input file exists and is readable.",
                "Make sure the file is CSV, NDJSON, or Parquet with the DSF-E required fields.",
                "If you are using Parquet, ensure the optional parquet dependency is installed.",
                "Re-run with --wizard if you want the CLI to walk through the inputs again.",
            ],
        )
        print(palette.error("Validation could not start."))
        print(palette.warning(str(exc)))
        print(json.dumps(payload, indent=2))
        return 2
    _print_human_summary(summary, palette)
    print(json.dumps(summary, indent=2))
    return 1 if summary["error_count"] else 0


def _collect_cli_config(
    *,
    wizard: bool,
    input_file: Path | None,
    output_dir: Path | None,
    palette: Palette,
) -> ParserConfig | None:
    if not wizard:
        if input_file is None or output_dir is None:
            raise ValueError("input_file and output_dir are required in quick mode.")
        return {"input_file": input_file, "output_dir": output_dir}

    print_banner(
        palette,
        "DSF-E Pre-flight Validator",
        "Guided mode helps first-time users. Veteran users can skip this with positional arguments.",
    )
    chosen_input = Path(prompt_text("Input file path", default=str(input_file or "")))
    chosen_output = Path(
        prompt_text("Output directory", default=str(output_dir or "out\\preflight"))
    )
    print()
    print_kv(palette, "Input", str(chosen_input))
    print_kv(palette, "Output", str(chosen_output))
    print()
    action = prompt_choice(
        "Choose your next step.",
        {"r": "run validation", "e": "edit paths", "q": "quit"},
        default="r",
    )
    if action == "q":
        return None
    if action == "e":
        return _collect_cli_config(
            wizard=True,
            input_file=chosen_input,
            output_dir=chosen_output,
            palette=palette,
        )
    if not confirm("Start validation now?", default=True):
        return None
    return {"input_file": chosen_input, "output_dir": chosen_output}


def _print_human_summary(summary: dict[str, object], palette: Palette) -> None:
    print()
    heading = "Validation passed" if not summary["error_count"] else "Validation found issues"
    status = palette.success(heading) if not summary["error_count"] else palette.warning(heading)
    print(status)
    print_kv(palette, "Records", str(summary["records_processed"]))
    print_kv(palette, "Errors", str(summary["error_count"]))
    print_kv(palette, "Warnings", str(summary["warning_count"]))
    outputs = summary.get("outputs", {})
    if isinstance(outputs, dict):
        for label, path in outputs.items():
            print_kv(palette, label, str(path))
    print()


if __name__ == "__main__":
    raise SystemExit(main())
