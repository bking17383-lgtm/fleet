#!/usr/bin/env python3
"""Watch phone/inbox/ → phone/PENDING_FOR_CAPTN.md (CAPTN reads on wake)."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
INBOX = DRIVE / "phone/inbox"
PENDING = DRIVE / "phone/PENDING_FOR_CAPTN.md"
STATE = DRIVE / "phone/scanner_state.json"
LOG = DRIVE / "phone/scanner_log.txt"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _load() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"files": {}}


def _save(state: dict) -> None:
    state["last_scan"] = _now()
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _log(msg: str) -> None:
    line = f"{_now()} {msg}\n"
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
    print(line, end="", flush=True)


def scan_once() -> int:
    state = _load()
    known: dict[str, float] = state.get("files", {})
    new = 0
    latest = None
    for path in sorted(INBOX.glob("said_*.json")):
        try:
            mt = path.stat().st_mtime
        except OSError:
            continue
        key = path.name
        if known.get(key) == mt:
            continue
        known[key] = mt
        new += 1
        try:
            latest = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    state["files"] = known
    _save(state)
    if latest:
        lines = [
            "# Phone — waiting for CAPTN",
            f"Updated: {_now()}",
            "",
            f"**Time:** {latest.get('time')}",
            f"**You said:** {latest.get('text', '')}",
            f"**Frame:** {latest.get('image') or 'none'}",
            "",
            "Reply: one line → `phone/say.txt` or http://127.0.0.1:8765/desk",
            "",
        ]
        PENDING.write_text("\n".join(lines), encoding="utf-8")
        _log(f"pending updated from {latest.get('id')}")
    return new


def main() -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    _log("radio_scanner start")
    while True:
        try:
            scan_once()
        except Exception as exc:
            _log(f"error: {exc}")
        time.sleep(15)


if __name__ == "__main__":
    main()
