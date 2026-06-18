#!/usr/bin/env python3
"""Sync pulse — Brian trigger word · everyone reads mtime.

  python3 ~/.stan/cpt_sync.py pulse
  python3 ~/.stan/cpt_sync.py fresh
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

PULSE = "fleet/bus/SYNC_PULSE.txt"
LAST = "fleet/bus/DADDY_LAST_POST.txt"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def pulse(note: str = "Brian sync") -> str:
    bus = bus_root()
    now = _now()
    text = f"SYNC_PULSE — {now}\nnote={note}\nread=fleet/SYNC_TRIGGERS.txt\nWord: SYNC\n"
    p = bus / PULSE
    safe_mkdir(p.parent)
    p.write_text(text, encoding="utf-8")
    return str(p)


def fresh() -> str:
    bus = bus_root()
    now = _now()
    line = f"DADDY LAST POST — {now}\ntrigger=fresh · repost orders on bus\nWord: FRESH\n"
    (bus / LAST).write_text(line, encoding="utf-8")
    pulse("fresh — Daddy reposting orders")
    return pulse("fresh")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pulse"
    note = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Brian sync"
    path = fresh() if cmd == "fresh" else pulse(note)
    print(f"→ {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
