#!/usr/bin/env python3
"""Alexa auto-speak — watch phone/say.txt · no browser tap needed.

  python3 ~/.stan/alexa_watch.py once   # speak if say.txt changed
  python3 ~/.stan/alexa_watch.py watch  # poll every 8s (background)

REAL_ALEXA=1 (or fleet/bus/REAL_ALEXA.txt): write phone/say.txt only — Echo in room speaks.
Otherwise tries espeak-ng on CB2, then say.txt.
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text, STAN, LOGS

STATE = STAN / "alexa_watch_state.txt"
LOG = LOGS / "alexa_watch.log"
INTERVAL = float(os.environ.get("ALEXA_WATCH_SEC", "8"))


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    line = f"{datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')} {msg}\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _say_path() -> Path:
    bus = bus_root()
    for rel in ("phone/say.txt", "fleet/bus/AWS_SPEAK_ALOUD.txt"):
        p = bus / rel
        if safe_is_file(p):
            t = safe_read_text(p).strip()
            if t and not t.startswith("("):
                return p
    return bus / "phone/say.txt"


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:16]


def _last_fp() -> str:
    if not STATE.is_file():
        return ""
    return STATE.read_text(encoding="utf-8").strip().splitlines()[0] if STATE.read_text().strip() else ""


def _save_fp(fp: str, method: str) -> None:
    safe_mkdir(STAN)
    STATE.write_text(f"{fp}\n{method}\n{datetime.now(timezone.utc).astimezone().isoformat()}\n", encoding="utf-8")


def _afk_silent() -> bool:
    bus = bus_root()
    p = bus / "fleet/bus/DADDY_SILENT_UNTIL.txt"
    if not safe_is_file(p):
        return False
    try:
        line = safe_read_text(p).strip().splitlines()[0]
        until = datetime.fromisoformat(line)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc).astimezone()
        return datetime.now(timezone.utc).astimezone() < until
    except (ValueError, IndexError, OSError):
        return False


def tick() -> str:
    if _afk_silent():
        return "afk silent"
    p = _say_path()
    if not safe_is_file(p):
        return "no say.txt"
    text = safe_read_text(p).strip()
    if not text or text.startswith("("):
        return "empty"
    fp = _fingerprint(text)
    if fp == _last_fp():
        return "unchanged"
    sys.path.insert(0, str(STAN))
    from aws_speech import speak  # noqa: WPS433

    method = speak(text)
    _save_fp(fp, method)
    _log(f"spoke via {method}: {text[:80]}")
    return method


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        _log("watch start")
        while True:
            try:
                tick()
            except Exception as exc:
                _log(f"err {exc}")
            time.sleep(INTERVAL)
    else:
        print(tick())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
