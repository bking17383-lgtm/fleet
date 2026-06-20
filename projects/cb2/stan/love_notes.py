#!/usr/bin/env python3
"""Free love notes — store + share links."""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, safe_mkdir

WALL = STAN / "love_wall" / "notes.json"
MAX_NOTES = 500
MAX_LEN = 600


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load() -> list[dict]:
    if not WALL.is_file():
        return []
    try:
        return json.loads(WALL.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(notes: list[dict]) -> None:
    safe_mkdir(WALL.parent)
    WALL.write_text(json.dumps(notes[-MAX_NOTES:], indent=0), encoding="utf-8")


def _clean(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s[:n]


def create(to: str, message: str, from_name: str = "") -> dict:
    note_id = secrets.token_urlsafe(8)
    entry = {
        "id": note_id,
        "to": _clean(to, 80),
        "message": _clean(message, MAX_LEN),
        "from": _clean(from_name, 60),
        "created": _now(),
    }
    notes = _load()
    notes.append(entry)
    _save(notes)
    return entry


def get(note_id: str) -> dict | None:
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,24}", note_id or ""):
        return None
    for n in _load():
        if n.get("id") == note_id:
            return n
    return None
