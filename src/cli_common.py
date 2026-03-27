from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PromptFn = Callable[[str], str]


@dataclass(frozen=True)
class Palette:
    enabled: bool = True

    def color(self, text: str, code: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def title(self, text: str) -> str:
        return self.color(text, "1;36")

    def success(self, text: str) -> str:
        return self.color(text, "1;32")

    def warning(self, text: str) -> str:
        return self.color(text, "1;33")

    def error(self, text: str) -> str:
        return self.color(text, "1;31")

    def info(self, text: str) -> str:
        return self.color(text, "36")

    def accent(self, text: str) -> str:
        return self.color(text, "35")


def print_banner(palette: Palette, title: str, subtitle: str) -> None:
    print(palette.title(title))
    print(palette.info(subtitle))
    print()


def print_kv(palette: Palette, label: str, value: str) -> None:
    print(f"{palette.accent(label + ':'):18} {value}")


def prompt_text(prompt: str, *, default: str = "", input_fn: PromptFn | None = None) -> str:
    active_input = input_fn or input
    suffix = f" [{default}]" if default else ""
    raw = active_input(f"{prompt}{suffix}: ").strip()
    return raw or default


def prompt_choice(
    prompt: str,
    options: dict[str, str],
    *,
    default: str,
    input_fn: PromptFn | None = None,
) -> str:
    active_input = input_fn or input
    option_text = ", ".join(f"[{key.upper()}] {label}" for key, label in options.items())
    while True:
        raw = active_input(f"{prompt} {option_text} [{default.upper()}]: ").strip().lower()
        choice = raw or default.lower()
        if choice in options:
            return choice
        print("Please choose one of the highlighted hotkeys.")


def confirm(prompt: str, *, default: bool = True, input_fn: PromptFn | None = None) -> bool:
    default_key = "y" if default else "n"
    choice = prompt_choice(
        prompt,
        {"y": "yes", "n": "no"},
        default=default_key,
        input_fn=input_fn,
    )
    return choice == "y"


def build_error_payload(
    *,
    tool: str,
    exc: Exception,
    inputs: dict[str, Path | bool | str | None],
    hints: list[str],
) -> dict[str, object]:
    return {
        "status": "fatal_error",
        "tool": tool,
        "message": str(exc),
        "details": {
            "exception_type": type(exc).__name__,
            "inputs": {key: str(value) for key, value in inputs.items() if value not in {None, ""}},
        },
        "next_steps": hints,
    }
