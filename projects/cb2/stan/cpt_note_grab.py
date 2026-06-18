#!/usr/bin/env python3
"""GRAB Brian broadcasts — mesh phone/inbox, GL inbox, lester transcripts → bus."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

OUT = "fleet/bus/BRIAN_BROADCAST.txt"
MAX_ITEMS = 12


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _phone_notes(bus: Path) -> list[tuple[str, str, str]]:
    inbox = bus / "phone/inbox"
    if not inbox.is_dir():
        return []
    rows: list[tuple[str, str, str]] = []
    for path in sorted(inbox.glob("said_*.json"))[-MAX_ITEMS:]:
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        text = (d.get("text") or "").strip()
        if text:
            rows.append((d.get("time") or path.stem, "mesh", text))
    return rows


def _glob_notes(bus: Path, pattern: str, label: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for path in sorted(bus.glob(pattern))[-6:]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if text:
            ts = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
            rows.append((ts, label, text[:500]))
    return rows


def grab() -> str:
    bus = bus_root()
    rows = _phone_notes(bus)
    rows.extend(_glob_notes(bus, "inbox/live_*.txt", "gl-inbox"))
    rows.extend(_glob_notes(bus, "drop_pile/from_lester/live_transcript_*.txt", "sink"))
    rows.extend(_glob_notes(bus, "drop_pile/from_lester/live_*.txt", "save"))

    pending = bus / "phone/PENDING_FOR_CAPTN.md"
    if pending.is_file():
        try:
            pt = pending.read_text(encoding="utf-8", errors="replace")
            if "**You said:**" in pt:
                for ln in pt.splitlines():
                    if ln.startswith("**You said:**"):
                        rows.append((_now(), "pending", ln.replace("**You said:**", "").strip()))
                        break
        except OSError:
            pass

    rows = rows[-MAX_ITEMS:]
    lines = [
        f"BRIAN BROADCAST — {_now()}",
        f"count={len(rows)} · CPT GRAB this file every session",
        "",
    ]
    if not rows:
        lines.append("(no broadcasts found — check mesh :8765 · puppy sink :8766)")
    else:
        for ts, src, text in rows:
            one = " ".join(text.split())
            lines.append(f"[{src}] {ts}")
            lines.append(f"  {one[:400]}")
            lines.append("")

    body = "\n".join(lines).rstrip() + "\n"
    out = bus / OUT
    safe_mkdir(out.parent)
    out.write_text(body, encoding="utf-8")
    return body


def main() -> int:
    print(grab())
    print(f"→ {bus_root() / OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
