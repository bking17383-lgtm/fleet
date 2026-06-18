#!/usr/bin/env python3
"""BEACON — every box reports to CPT on one bus file.

  python3 ~/.stan/beacon_pulse.py              # auto role from hostname/key
  python3 ~/.stan/beacon_pulse.py NET
  python3 ~/.stan/beacon_pulse.py STUDIO
  python3 ~/.stan/beacon_pulse.py CPT
  python3 ~/.stan/beacon_pulse.py BEACON      # CB2 alias

Appends: fleet/bus/BEACON_PULSE.txt
Also: role outbox (puppy_outbox · mac_outbox · SLAVE_PULSE)
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

PULSE = "fleet/bus/BEACON_PULSE.txt"
OUTBOX = {
    "NET": "fleet/bus/puppy_outbox.txt",
    "STUDIO": "fleet/bus/mac_outbox.txt",
    "CPT": "fleet/bus/SLAVE_PULSE.txt",
    "BEACON": "fleet/bus/SLAVE_PULSE.txt",
}

ALIASES = {
    "BEACON": "CPT",
    "CPT_SLAVE": "CPT",
    "CAPTN": "CPT",
    "DADDY": "CPT",
    "UNCLE": "STUDIO",
    "WRANGLER": "STUDIO",
    "PLATE": "NET",
    "PUPPY": "NET",
}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _ip() -> str:
    try:
        out = subprocess.getoutput("hostname -I").split()
        return out[0] if out else "?"
    except OSError:
        return "?"


def _guess_role(host: str) -> str:
    h = host.lower()
    if "puppy" in h:
        return "NET"
    if "cb1" in h or "studio" in h:
        return "STUDIO"
    return "CPT"


def pulse(role: str) -> str:
    role = ALIASES.get(role.upper(), role.upper())
    if role not in OUTBOX:
        print("Usage: beacon_pulse.py [NET|STUDIO|CPT|BEACON]", file=sys.stderr)
        return ""
    bus = bus_root()
    host = socket.gethostname()
    ip = _ip()
    now = _now()
    line = f"BEACON — {role} — {host} — {ip} — {now}\n"

    p = bus / PULSE
    safe_mkdir(p.parent)
    with open(p, "a", encoding="utf-8") as f:
        f.write(line)

    ob = bus / OUTBOX[role]
    safe_mkdir(ob.parent)
    with open(ob, "a", encoding="utf-8") as f:
        f.write(line)

    print(line.strip())
    print(f"→ {p}")
    return line


def main() -> int:
    role = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BEACON_ROLE", "")).upper()
    if not role:
        role = _guess_role(socket.gethostname())
    if not pulse(role):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
