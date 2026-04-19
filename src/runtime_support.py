from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class RuntimeSettings:
    tool: str
    profile: str
    correlation_id: str
    log_level: str
    redact_logs: bool
    audit_log_path: Path | None


@dataclass(frozen=True)
class AppError(Exception):
    code: str
    message: str
    details: dict[str, object] | None = None

    def __str__(self) -> str:
        return self.message


def load_runtime_settings(
    *,
    tool: str,
    profile: str | None = None,
    correlation_id: str | None = None,
) -> RuntimeSettings:
    chosen_profile = profile or os.getenv("CLINICALAI_PROFILE", "local")
    chosen_correlation_id = correlation_id or os.getenv("CLINICALAI_CORRELATION_ID") or str(uuid4())
    log_level = os.getenv("CLINICALAI_LOG_LEVEL", "INFO").upper()
    audit_path_value = os.getenv("CLINICALAI_AUDIT_LOG")
    return RuntimeSettings(
        tool=tool,
        profile=chosen_profile,
        correlation_id=chosen_correlation_id,
        log_level=log_level,
        redact_logs=_env_flag("CLINICALAI_REDACT_LOGS", default=True),
        audit_log_path=Path(audit_path_value) if audit_path_value else None,
    )


def emit_structured_log(
    settings: RuntimeSettings,
    *,
    level: str,
    event: str,
    payload: dict[str, Any] | None = None,
) -> None:
    body = {
        "timestamp": datetime.now(UTC).isoformat(),
        "tool": settings.tool,
        "profile": settings.profile,
        "level": level.upper(),
        "event": event,
        "correlation_id": settings.correlation_id,
        "payload": payload or {},
    }
    if settings.redact_logs:
        body = _redact_mapping(body)
    print(json.dumps(body, ensure_ascii=False, default=str), file=sys.stderr)


def append_audit_event(path: Path | None, event: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"timestamp": datetime.now(UTC).isoformat(), **event}, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def classify_error(tool: str, exc: Exception) -> AppError:
    message = str(exc)
    if isinstance(exc, AppError):
        return exc
    if isinstance(exc, OSError):
        return AppError(code=f"{tool.upper()}_IO_ERROR", message=message)
    if "does not exist" in message.lower():
        return AppError(code=f"{tool.upper()}_NOT_FOUND", message=message)
    if "json could not be parsed" in message.lower() or "ndjson parsing failed" in message.lower():
        return AppError(code=f"{tool.upper()}_PARSE_ERROR", message=message)
    if "missing required" in message.lower():
        return AppError(code=f"{tool.upper()}_SCHEMA_ERROR", message=message)
    return AppError(code=f"{tool.upper()}_RUNTIME_ERROR", message=message)


def _env_flag(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _redact_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_mapping(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_redact_mapping(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _redact_text(text: str) -> str:
    redacted = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[REDACTED_EMAIL]", text)
    redacted = re.sub(r"\b\d{8,}\b", "[REDACTED_ID]", redacted)
    return redacted
