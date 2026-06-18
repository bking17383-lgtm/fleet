#!/usr/bin/env python3
"""Daddy announces to team before/during any action — no silent bus writes."""
from __future__ import annotations

import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

BUS = bus_root()
ACTIVITY = BUS / "fleet/bus/TEAM_ACTIVITY.txt"
DOING_NOW = BUS / "fleet/bus/DADDY_DOING_NOW.txt"
MAC = BUS / "fleet/bus/mac_inbox.txt"
MARKER = "--- DADDY ACTIVITY ---"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _host() -> str:
    return socket.gethostname()


def announce(action: str, detail: str = "", *, targets: str = "all") -> str:
    """Tell Uncle · Gem · Puppy · Brian what Daddy is doing right now."""
    now = _now()
    host = _host()
    head = f"[{now}] DADDY on {host}"
    line = f"{head}: {action.strip()}"
    if detail.strip():
        line += f" — {detail.strip()}"
    if targets != "all":
        line += f" (→ {targets})"

    safe_mkdir(ACTIVITY.parent)
    prev = ACTIVITY.read_text(encoding="utf-8", errors="replace") if ACTIVITY.is_file() else ""
    if MARKER not in prev:
        prev = f"TEAM ACTIVITY — Daddy announces every action\n{MARKER}\n\n"
    head_part, _, tail = prev.partition(MARKER)
    block = tail.strip().splitlines()
    block.append(line)
    block = block[-40:]
    ACTIVITY.write_text(
        f"{head_part}{MARKER}\n\n" + "\n".join(block) + "\n",
        encoding="utf-8",
    )

    DOING_NOW.write_text(
        f"DADDY DOING NOW — {now}\n"
        f"action: {action.strip()}\n"
        f"detail: {detail.strip() or '(none)'}\n"
        f"targets: {targets}\n"
        f"read: fleet/bus/TEAM_ACTIVITY.txt\n",
        encoding="utf-8",
    )

    try:
        stamp = now[:16].replace("T", " ")
        note = (
            f"--- from: Daddy announce | {stamp} ---\n"
            f"DADDY: {action.strip()}\n"
            f"{detail.strip()}\n"
            f"team: fleet/bus/DADDY_DOING_NOW.txt\n"
        )
        old = MAC.read_text(encoding="utf-8", errors="replace") if MAC.is_file() else ""
        MAC.write_text(note + old[:4000], encoding="utf-8")
    except OSError:
        pass

    return line


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: daddy_team_say.py <action> [detail] [targets]", file=sys.stderr)
        return 1
    action = sys.argv[1]
    detail = sys.argv[2] if len(sys.argv) > 2 else ""
    targets = sys.argv[3] if len(sys.argv) > 3 else "all"
    print(announce(action, detail, targets=targets))
    print(f"→ {ACTIVITY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
