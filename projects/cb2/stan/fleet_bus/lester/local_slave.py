#!/usr/bin/env python3
"""Local slave — keyed pulse + read orders. Any box. Fast."""
from __future__ import annotations

import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root

ROLES = {
    "NET": ("5f54badb", "fleet/orders/PUPPY_ORDERS.txt", "fleet/bus/puppy_outbox.txt"),
    "STUDIO": ("93fec320", "fleet/orders/CB1_ORDERS.txt", "fleet/bus/mac_outbox.txt"),
    "CPT_SLAVE": ("f770e0dc", "fleet/orders/CB2_ORDERS.txt", "fleet/bus/SLAVE_PULSE.txt"),
}
# Machine name = wakeup word (say in Cursor or Gemini)
ALIASES = {
    "BEACON": "CPT_SLAVE",
    "CPT": "CPT_SLAVE",
    "CAPTN": "CPT_SLAVE",
    "CAPTAIN": "CPT_SLAVE",
    "DADDY": "CPT_SLAVE",
    "SLAVE": "CPT_SLAVE",
    "PUPPY": "NET",
    "NET": "NET",
    "UNCLE": "STUDIO",
    "STUDIO": "STUDIO",
    "GEM": "STUDIO",
}


def _drive() -> Path | None:
    root = bus_root()
    return root if (root / "fleet").is_dir() else None


def _key(role: str) -> str | None:
    env = Path.home() / ".stan/slave.key"
    if env.is_file():
        return env.read_text(encoding="utf-8").strip().splitlines()[0]
    return os.environ.get(f"{role}_KEY") or os.environ.get("SLAVE_KEY")


def main() -> int:
    role = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SLAVE_ROLE", "")).upper()
    role = ALIASES.get(role, role)
    if role not in ROLES:
        print("Usage: local_slave.py NET|STUDIO|CPT_SLAVE")
        print("(BEACON/CPT/CAPTN/DADDY → CPT_SLAVE · retired names)")
        return 1
    expect, orders_rel, out_rel = ROLES[role]
    key = _key(role)
    if key != expect:
        print(f"BAD KEY for {role}")
        return 1
    drive = _drive()
    host = socket.gethostname()
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    if not drive:
        print(f"NO BUS — {role} {host} {now} (run slave_boot.sh)")
        return 2
    orders = drive / orders_rel
    print(f"OK {role} key={key[:4]}… host={host}")
    if orders.is_file():
        print("--- orders (first 12 lines) ---")
        print("\n".join(orders.read_text(encoding="utf-8", errors="replace").splitlines()[:12]))
    pulse = drive / "fleet/bus/SLAVE_PULSE.txt"
    pulse.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{now}] {role} key_ok host={host}\n"
    with open(pulse, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"pulse → {pulse}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
