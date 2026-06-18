#!/usr/bin/env python3
"""Alexa learn mode — listen and save · no execute just now."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text

try:
    from george_memory import upgrade_from_heard
except ImportError:
    def upgrade_from_heard(text: str) -> dict:  # type: ignore[misc]
        return {"ok": False, "error": "no george_memory"}

MODE_FILE = "fleet/bus/ALEXA_LEARN_MODE.txt"
LEARN_LOG = "fleet/bus/ALEXA_LEARN.jsonl"
HEARD_TAIL = "phone/heard.txt"
HEARD_MAX = 40


def learn_mode() -> bool:
    """True = capture only · no AWS / no fleet execute."""
    if os.environ.get("ALEXA_LEARN", "").strip() in ("0", "no", "false", "off", "execute"):
        return False
    if os.environ.get("ALEXA_LEARN", "").strip() in ("1", "yes", "true", "on", "learn"):
        return True
    bus = bus_root()
    path = bus / MODE_FILE
    if not safe_is_file(path):
        return True
    for line in safe_read_text(path).splitlines():
        s = line.strip().lower()
        if not s or s.startswith("#"):
            continue
        if s.startswith("learn=0") or s.startswith("execute=1") or s.startswith("execute=on"):
            return False
        if s.startswith("learn=1") or s.startswith("listen=1"):
            return True
    return True


def hear(text: str, *, source: str = "voice") -> dict:
    """Append one heard line for later review."""
    msg = text.strip()
    if not msg:
        return {"ok": False, "error": "empty"}

    bus = bus_root()
    now = datetime.now(timezone.utc).astimezone()
    entry = {
        "time": now.isoformat(timespec="seconds"),
        "source": source,
        "text": msg,
        "mode": "learn",
    }

    log_path = bus / LEARN_LOG
    safe_mkdir(log_path.parent)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    heard_path = bus / HEARD_TAIL
    safe_mkdir(heard_path.parent)
    prior = safe_read_text(heard_path).splitlines() if safe_is_file(heard_path) else []
    prior = [ln for ln in prior if ln.strip()]
    prior.append(f"[{entry['time']}] {msg}")
    heard_path.write_text("\n".join(prior[-HEARD_MAX:]) + "\n", encoding="utf-8")

    stamp = bus / "fleet/bus/GEORGE_LAST_HEARD.txt"
    stamp.write_text(
        f"GEORGE_LAST_HEARD — {entry['time']}\nsource={source}\ntext={msg}\nmode=learn\n",
        encoding="utf-8",
    )
    upgrade = upgrade_from_heard(msg)
    return {"ok": True, "upgrade": upgrade, **entry}


def recent(limit: int = 12) -> list[dict]:
    bus = bus_root()
    path = bus / LEARN_LOG
    if not safe_is_file(path):
        return []
    lines = [ln.strip() for ln in safe_read_text(path).splitlines() if ln.strip()]
    out: list[dict] = []
    for ln in lines[-limit:]:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out
