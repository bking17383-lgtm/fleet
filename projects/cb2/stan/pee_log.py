#!/usr/bin/env python3
"""Pee game log — 30m reminder lane for hitme.dev/pee."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, safe_mkdir

DATA = STAN / "pee_wall" / "log.json"
REMIND_MINUTES = 30
GALLONS_PER_PEE = 1.6
MAX_EVENTS = 500


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load() -> dict:
    if not DATA.is_file():
        return {"events": []}
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"events": []}


def _save(data: dict) -> None:
    safe_mkdir(DATA.parent)
    events = data.get("events") or []
    if len(events) > MAX_EVENTS:
        data["events"] = events[-MAX_EVENTS:]
    DATA.write_text(json.dumps(data, indent=0), encoding="utf-8")


def log_pee(*, source: str = "pee", note: str = "") -> dict:
    data = _load()
    events = data.get("events") or []
    events.append(
        {
            "at": _now(),
            "source": (source or "pee")[:20],
            "note": (note or "")[:80],
        }
    )
    data["events"] = events
    _save(data)
    return status()


def status() -> dict:
    data = _load()
    events = data.get("events") or []
    n = len(events)
    last_at = events[-1]["at"] if events else None
    minutes_since = None
    due = False
    if last_at:
        try:
            t = datetime.fromisoformat(last_at)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc).astimezone() - t.astimezone()
            minutes_since = max(0, int(delta.total_seconds() // 60))
            due = minutes_since >= REMIND_MINUTES
        except ValueError:
            pass
    gallons = round(n * GALLONS_PER_PEE, 1)
    return {
        "ok": True,
        "count": n,
        "last_at": last_at,
        "minutes_since": minutes_since,
        "remind_minutes": REMIND_MINUTES,
        "due": due,
        "due_question": "Do you have to pee yet?" if due else None,
        "gallons_saved": gallons,
    }
