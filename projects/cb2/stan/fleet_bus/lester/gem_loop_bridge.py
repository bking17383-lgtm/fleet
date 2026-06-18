#!/usr/bin/env python3
"""CB1 — Gem/Uncle bridge. Reads Daddy ping · writes gem_to_cpt · runs uncle_exec."""
from __future__ import annotations

import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BUS_CANDIDATES = [
    Path.home() / "GoogleDrive/MyDrive",
    Path("/mnt/shared/GoogleDrive/MyDrive"),
    Path.home() / ".stan/fleet_bus",
]
STAN = Path.home() / ".stan"


def _bus() -> Path:
    for p in BUS_CANDIDATES:
        if (p / "fleet").is_dir():
            return p
    return BUS_CANDIDATES[-1]


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def main() -> int:
    bus = _bus()
    ping = bus / "fleet/bus/GEM_LOOP_PING.txt"
    to_gem = bus / "fleet/bus/cpt_to_gem.txt"
    from_gem = bus / "fleet/bus/gem_to_cpt.txt"
    host = socket.gethostname()
    if "penguin" in host.lower():
        msg = (
            f"GEM REFUSE — penguin is Daddy · not Gem — {_now()}\n"
            f"host: {host} · WRONG BOX\n"
            f"read: fleet/NAMING_LAW.txt · drop_pile/to_gemini/GEM_SELF_FIX.txt\n"
            f"uncle_exec blocked here · run gem_loop_bridge on Uncle box (CB1) only\n"
        )
        from_gem.parent.mkdir(parents=True, exist_ok=True)
        from_gem.write_text(msg, encoding="utf-8")
        print(msg, file=sys.stderr)
        return 2

    ip = subprocess.getoutput("hostname -I").split()[0] if subprocess.getoutput("hostname -I") else "?"
    now = _now()

    epoch = "?"
    if ping.is_file():
        for ln in ping.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("epoch="):
                epoch = ln.split("=", 1)[1].strip()

    gem_reply = (
        f"--- Gem → Daddy ---\n"
        f"time: {now}\n"
        f"host: {host}\n"
        f"read_ping_epoch: {epoch}\n"
        f"read_cpt_to_gem: {'YES' if to_gem.is_file() else 'NO'}\n"
        f"GEM ok — read ping {epoch} — {now}\n"
        f"next: uncle_exec on Uncle box only · not penguin\n"
    )
    from_gem.parent.mkdir(parents=True, exist_ok=True)
    from_gem.write_text(gem_reply, encoding="utf-8")
    print(gem_reply)
    print(f"→ {from_gem}")

    exec_sh = STAN / "uncle_exec.sh"
    if exec_sh.is_file():
        print("running uncle_exec.sh …")
        subprocess.run(["bash", str(exec_sh)], check=False)
    else:
        bus_exec = bus / "lester/uncle_exec.sh"
        if bus_exec.is_file():
            subprocess.run(["bash", str(bus_exec)], check=False)
        else:
            print("WARN: no uncle_exec.sh — post uncle_to_cpt manually")

    print(f"read Daddy ack: {bus / 'fleet/bus/cpt_ack_gem.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
