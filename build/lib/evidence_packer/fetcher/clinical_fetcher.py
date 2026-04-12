from __future__ import annotations

import json
from pathlib import Path

from evidence_packer.models.fhir_models import ClinicalNote


def load_clinical_notes(notes_dir: Path) -> list[ClinicalNote]:
    if not notes_dir.exists():
        raise ValueError(f"Clinical notes directory does not exist: {notes_dir}")
    if not notes_dir.is_dir():
        raise ValueError(f"Clinical notes path must be a directory: {notes_dir}")
    notes: list[ClinicalNote] = []
    for path in sorted(notes_dir.iterdir()):
        if path.is_dir():
            continue
        if path.suffix.lower() == ".txt":
            notes.append(ClinicalNote(source=path.name, text=path.read_text(encoding="utf-8")))
        elif path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                text = str(payload.get("text", "") or payload.get("note", "") or "")
                notes.append(ClinicalNote(source=path.name, text=text))
    if not notes:
        raise ValueError(
            "No usable clinical notes were found. Add .txt notes or JSON notes with a 'text' or 'note' field."
        )
    return notes
