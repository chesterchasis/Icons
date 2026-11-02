from __future__ import annotations

import sys
from pathlib import Path


def read_version() -> str:
    roots = []
    if getattr(sys, "frozen", False):
        roots.append(Path(getattr(sys, "_MEIPASS")))
    roots.append(Path(__file__).resolve().parents[1])
    for root in roots:
        candidate = root / "VERSION"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return "0.0.0"


__version__ = read_version()
