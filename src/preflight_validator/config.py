"""
Optional configuration loader for DSF-E rule parameters.

Reads ``config.toml`` (path from $CLINICAL_AI_CONFIG, else ./config.toml)
and overrides the hardcoded defaults in ``schemas/dsfe.py``. If no config
file is found, or a key is absent, the built-in defaults are used unchanged
â€” this module is purely additive and never required.

Why this exists: LOINC value sets, score thresholds, and follow-up windows
are payer/measure-year specific. Externalizing them to TOML lets a
deployment retune the validator without editing source.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python <3.11 fallback (not expected in prod)
    tomllib = None  # type: ignore[assignment]


def _find_config_path() -> Path | None:
    env_path = os.environ.get("CLINICAL_AI_CONFIG")
    if env_path:
        candidate = Path(env_path)
        return candidate if candidate.is_file() else None
    candidate = Path.cwd() / "config.toml"
    return candidate if candidate.is_file() else None


def _load_raw() -> dict:
    if tomllib is None:
        return {}
    path = _find_config_path()
    if path is None:
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def load_dsfe_overrides() -> dict[str, object]:
    """Return the ``[dsfe]`` table from config.toml, or {} if absent."""
    return _load_raw().get("dsfe", {})


def apply_overrides(
    *,
    approved_loinc_by_tool: dict[str, set[str]],
    thresholds: dict[str, int],
    follow_up_codes: set[str],
    follow_up_window_days: int,
) -> tuple[dict[str, set[str]], dict[str, int], set[str], int]:
    """
    Apply config.toml overrides on top of the given defaults.

    Returns a new tuple of (approved_loinc_by_tool, thresholds,
    follow_up_codes, follow_up_window_days). Any key absent from the
    config file (or the file itself) leaves the corresponding default
    untouched.
    """
    overrides = load_dsfe_overrides()

    loinc_override = overrides.get("approved_loinc_by_tool")
    if loinc_override:
        approved_loinc_by_tool = {
            tool: set(codes) for tool, codes in loinc_override.items()
        }

    thresholds_override = overrides.get("thresholds")
    if thresholds_override:
        thresholds = {tool: int(value) for tool, value in thresholds_override.items()}

    follow_up_codes_override = overrides.get("follow_up_codes")
    if follow_up_codes_override:
        follow_up_codes = set(follow_up_codes_override)

    follow_up_window_override = overrides.get("follow_up_window_days")
    if follow_up_window_override is not None:
        follow_up_window_days = int(follow_up_window_override)

    return approved_loinc_by_tool, thresholds, follow_up_codes, follow_up_window_days