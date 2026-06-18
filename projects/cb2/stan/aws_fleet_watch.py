#!/usr/bin/env python3
"""AWS watches fleet board · posts priorities for CPT · no captain steal."""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text, STAN, LOGS

LOG = LOGS / "aws_fleet_watch.log"
STATE = STAN / "aws_fleet_watch_state.json"

BOARD_FILES = (
    "fleet/bus/CPT_FOCUS.txt",
    "fleet/bus/CPT_DELEGATE_NOW.txt",
    "fleet/bus/CPT_SLAVE.txt",
    "fleet/bus/BRIAN_VITAL.txt",
    "fleet/bus/BRIAN_BROADCAST.txt",
    "fleet/bus/cpt_to_gem.txt",
    "fleet/bus/cpt_to_puppy.txt",
    "fleet/bus/gem_to_cpt.txt",
    "fleet/bus/puppy_outbox.txt",
    "fleet/STUCK_BOARD.txt",
    "fleet/FIRST_PRIORITY.txt",
)

PRIORITIES_OUT = "fleet/bus/AWS_FLEET_PRIORITIES.txt"
CPT_INBOX = "fleet/bus/CPT_AWS_INBOX.txt"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{_now()} {msg}\n")


def _board_fingerprint(bus: Path) -> str:
    parts: list[str] = []
    for rel in BOARD_FILES:
        p = bus / rel
        if not safe_is_file(p):
            parts.append(f"{rel}:missing")
            continue
        try:
            st = p.stat()
            parts.append(f"{rel}:{st.st_mtime_ns}:{st.st_size}")
        except OSError:
            parts.append(f"{rel}:err")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _first_meaningful(rel: str, bus: Path, n: int = 4) -> list[str]:
    p = bus / rel
    if not safe_is_file(p):
        return []
    lines = []
    for ln in safe_read_text(p).splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("---") or s.startswith("|"):
            continue
        if s.startswith("Word:") or s.startswith("Updated:"):
            continue
        lines.append(s[:140])
        if len(lines) >= n:
            break
    return lines


def _priorities(bus: Path) -> list[str]:
    out: list[str] = []
    stuck = _first_meaningful("fleet/STUCK_BOARD.txt", bus, 2)
    if stuck:
        out.append(f"stuck: {stuck[0]}")
    for rel, label in (
        ("fleet/FIRST_PRIORITY.txt", "first"),
        ("fleet/bus/CPT_DELEGATE_NOW.txt", "delegate"),
        ("fleet/bus/cpt_to_gem.txt", "gem-order"),
        ("fleet/bus/cpt_to_puppy.txt", "net-order"),
        ("fleet/bus/gem_to_cpt.txt", "gem-reply"),
    ):
        lines = _first_meaningful(rel, bus, 2)
        if lines:
            out.append(f"{label}: {lines[0]}")
    bc = _first_meaningful("fleet/bus/BRIAN_BROADCAST.txt", bus, 1)
    if bc:
        out.append(f"brian-broadcast: {bc[0][:120]}")
    pup = safe_read_text(bus / "fleet/bus/puppy_outbox.txt")
    if "DOWN" in pup or "FAIL" in pup:
        out.append("net: puppy needs attention")
    elif "clean" in pup.lower() or "RUNNING" in pup:
        out.append("net: puppy signal ok")
    return out[:8]


def watch_once() -> dict:
    bus = bus_root()
    fp = _board_fingerprint(bus)
    safe_mkdir(STAN)
    prev = {}
    if STATE.is_file():
        try:
            prev = json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    changed = fp != prev.get("fingerprint")
    pri = _priorities(bus)
    now = _now()

    pri_lines = [f"  • {p}" for p in pri] if pri else ["  • (none parsed)"]
    pri_body = "\n".join(
        [
            f"AWS_FLEET_PRIORITIES — {now}",
            "capt>> watches fleet board · build now via delegation · keep CPT available",
            f"board_fp={fp} changed={'YES' if changed else 'NO'}",
            "",
            "PRIORITIES:",
            *pri_lines,
            "",
            "Brian law: everything built now — delegate BUDDY/NET · CPT stays captain in Cursor",
            "CPT reads: fleet/bus/CPT_AWS_INBOX.txt · AWS_VITALS.txt · AWS_FLEET_PRIORITIES.txt",
        ]
    )
    out_pri = bus / PRIORITIES_OUT
    safe_mkdir(out_pri.parent)
    out_pri.write_text(pri_body + "\n", encoding="utf-8")

    inbox_lines = [
        f"CPT_AWS_INBOX — {now}",
        "from=AWS fleet watch · not captain",
        f"board_changed={'YES' if changed else 'NO'}",
        "",
    ]
    if changed:
        inbox_lines.append("NEW on fleet board — CPT glance when free:")
        inbox_lines.extend(f"  • {p}" for p in pri[:5])
    else:
        inbox_lines.append("no board change since last watch")
        if pri:
            inbox_lines.append("current top:")
            inbox_lines.append(f"  • {pri[0]}")
    inbox_lines.append("")
    inbox_lines.append("AWS handles speech · watch · vitals — Brian talks CPT in Cursor for orders")

    out_inbox = bus / CPT_INBOX
    out_inbox.write_text("\n".join(inbox_lines) + "\n", encoding="utf-8")

    STATE.write_text(
        json.dumps({"fingerprint": fp, "last_watch": now, "priorities": pri}, indent=2) + "\n",
        encoding="utf-8",
    )
    _log(f"watch fp={fp} changed={changed} n={len(pri)}")
    return {"changed": changed, "fingerprint": fp, "priorities": pri, "now": now}


def watch_loop(interval: float = 60.0) -> None:
    _log(f"START interval={interval}s")
    while True:
        try:
            watch_once()
        except Exception as exc:
            _log(f"ERR {exc}")
        time.sleep(interval)


def main() -> int:
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once":
        r = watch_once()
        print(json.dumps(r, indent=2))
        print(f"→ {bus_root() / PRIORITIES_OUT}")
        return 0
    if cmd == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
        watch_loop(sec)
        return 0
    print("Usage: aws_fleet_watch.py once|watch [seconds]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
