#!/usr/bin/env python3
"""Fleet stamps — nobody waits blind. One glance on bus + /goal.

  python3 ~/.stan/cpt_stamp.py doing daddy "ALEXA quick" --wait gem
  python3 ~/.stan/cpt_stamp.py ready daddy "in chat for Brian"
  python3 ~/.stan/cpt_stamp.py done gem "Alexa say.txt clean"
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

LANES = ("DADDY", "GEM", "UNCLE", "DOG")
OUT = "fleet/bus/STAMPS.txt"
CPT = "fleet/bus/CPT_STAMP.txt"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def stamp(lane: str, status: str, doing: str, waiting: str = "") -> str:
    bus = bus_root()
    lane = lane.upper()
    now = _now()
    if lane not in LANES:
        lane = "DADDY"
    status = status.upper()
    wait_bit = f" · waiting={waiting}" if waiting else ""
    line = f"{lane} {status} — {doing}{wait_bit} — {now}"

    # Read existing stamps, replace this lane
    board: dict[str, str] = {ln: "" for ln in LANES}
    p = bus / OUT
    if p.is_file():
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.strip()
            if not s or s.startswith("#") or s.startswith("STAMPS"):
                continue
            key = s.split()[0].upper()
            if key in board:
                board[key] = s

    board[lane] = line
    lines = [
        f"STAMPS — {now}",
        "LAW: if you are waiting and no stamp → ping Daddy · we are doing it wrong",
        "",
    ]
    for ln in LANES:
        if board[ln]:
            lines.append(board[ln])
    text = "\n".join(lines) + "\n"
    safe_mkdir(p.parent)
    p.write_text(text, encoding="utf-8")

    if lane == "DADDY":
        (bus / CPT).write_text(line + "\n", encoding="utf-8")

    return line


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: cpt_stamp.py <doing|ready|done|blocked> <lane> <text> [--wait NAME]")
        return 1
    status = sys.argv[1]
    lane = sys.argv[2]
    args = sys.argv[3:]
    waiting = ""
    if "--wait" in args:
        i = args.index("--wait")
        if i + 1 < len(args):
            waiting = args[i + 1]
        args = args[:i]
    doing = " ".join(args)
    line = stamp(lane, status, doing, waiting)
    print(line)
    print(f"→ {bus_root() / OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
