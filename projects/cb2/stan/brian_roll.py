#!/usr/bin/env python3
"""Brian idea board — analyze · roll · show fruition (Daddy lane only).

  python3 ~/.stan/brian_roll.py analyze   # refresh IDEAS_READY from IDEAS.txt
  python3 ~/.stan/brian_roll.py roll      # pick one analyzed idea
  python3 ~/.stan/brian_roll.py board     # print fruition board summary
"""
from __future__ import annotations

import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir, safe_read_text

IDEAS = "fleet/bus/IDEAS.txt"
READY = "fleet/bus/IDEAS_READY.txt"
BOARD = "fleet/bus/FRUITION_BOARD.txt"
ROLL_LOG = "fleet/bus/ROLL_LAST.txt"

# Analyst heuristics (Daddy · no Gem interrupt)
VERDICT_RULES = [
    (r"sarah|appointment|voice", "MONEY-A", "joy+money · Sarah link live on cb1"),
    (r"hitme|landing|domain", "MONEY-B", "money · hitme page + contact"),
    (r"card|collx|baseball|jailbreak|grade|scan", "MONEY-C", "money · 497 cards · scan live cb1"),
    (r"heritage|demo", "SHIP", "demo ready · card_demo.html"),
    (r"story|game|mine", "PARK", "blocked export · catalog later"),
    (r"mesh|radio|rover|network", "LIVE", "infra done · Gem sprint"),
    (r"aws|bedrock", "LIVE", "AWS independent · talk works"),
    (r"sell your baby|satire", "FUN", "creative · park until ship lane picks"),
    (r"readsy|playwright", "PARK", "needs Brian readsy ready"),
    (r"lester|export|gdoc", "NEEDS-GEM", "Gem lane when free · not now"),
]


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _analyze_line(line: str) -> tuple[str, str]:
    low = line.lower()
    for pat, verdict, note in VERDICT_RULES:
        if re.search(pat, low):
            return verdict, note
    if len(line.strip()) < 12:
        return "SKIP", "too short"
    return "PARK", "analyze manually"


def analyze() -> str:
    bus = bus_root()
    raw = safe_read_text(bus / IDEAS)
    entries: list[str] = []
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("---"):
            continue
        if s.startswith("["):
            verdict, note = _analyze_line(s)
            entries.append(f"{verdict} | {note} | {s[:120]}")
    header = f"IDEAS READY — analyzed {_now()}\nAnalyst: Daddy · Gem lane HOLD\n\n"
    body = "\n".join(entries) if entries else "(no ideas parsed)"
    text = header + body + "\n"
    (bus / READY).write_text(text, encoding="utf-8")
    return text


def roll() -> str:
    bus = bus_root()
    ready = safe_read_text(bus / READY)
    pool = [
        ln for ln in ready.splitlines()
        if ln.strip() and not ln.startswith("IDEAS") and not ln.startswith("Analyst")
        and "SKIP" not in ln
    ]
    if not pool:
        analyze()
        ready = safe_read_text(bus / READY)
        pool = [ln for ln in ready.splitlines() if "|" in ln and not ln.startswith("IDEAS")]
    pick = random.choice(pool) if pool else "(empty deck — add IDEAS.txt)"
    now = _now()
    out = f"ROLL — {now}\n{pick}\n\nSay roll again · or build this one with Daddy in chat.\n"
    safe_mkdir((bus / ROLL_LOG).parent)
    (bus / ROLL_LOG).write_text(out, encoding="utf-8")
    print(out)
    return out


def board() -> str:
    bus = bus_root()
    text = safe_read_text(bus / BOARD)
    print(text or "(no fruition board)")
    return text


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "board"
    if cmd == "analyze":
        print(analyze())
    elif cmd == "roll":
        roll()
    else:
        board()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
