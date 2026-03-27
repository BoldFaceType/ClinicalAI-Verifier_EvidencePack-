from __future__ import annotations

import shutil
import uuid
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parents[1] / ".test_runs"


def make_temp_dir(name: str) -> Path:
    path = TEST_ROOT / f"{name}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def cleanup_temp_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
