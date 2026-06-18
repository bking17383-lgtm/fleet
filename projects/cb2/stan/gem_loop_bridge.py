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
    )
    cpt_body = to_gem.read_text(encoding="utf-8", errors="replace") if to_gem.is_file() else ""
    buddy_job = "BRIAN JOB" in cpt_body or "BUDDY" in cpt_body
    if buddy_job and "Brian asked" in cpt_body:
        ask = ""
        for ln in cpt_body.splitlines():
            if "hibernat" in ln.lower() or ln.strip().startswith("gem "):
                ask = ln.strip()[:120]
                break
        gem_reply += f"GEM STALL — Chrome agent not working — {now}\n"
        if ask:
            gem_reply += f"Brian asked: {ask}\n"
        gem_reply += (
            "FIX: open Drive root insomniac.txt · paste into CB1 Chrome Cursor\n"
            "POST: BUDDY ok + GEM_UNDERSTAND.txt · not loop spam\n"
        )
    else:
        gem_reply += f"GEM ok — read ping {epoch} — {now}\n"
    gem_reply += "next: Chrome Gem reads cpt_to_gem · Uncle runs stay_awake\n"

    prev = ""
    if from_gem.is_file():
        prev = from_gem.read_text(encoding="utf-8", errors="replace")
    understand = bus / "fleet/bus/GEM_UNDERSTAND.txt"
    if understand.is_file() and "BUDDY ok" in understand.read_text(encoding="utf-8", errors="replace"):
        if "GEM ok — CPT loop" in prev or "GEM STALL" in prev or len(prev) < 120:
            gem_reply = (
                f"--- Gem → Daddy ---\n"
                f"time: {now}\n"
                f"host: {host}\n"
                f"BUDDY ok — stay awake fix posted — {now}\n"
                f"host: cb1 · not penguin\n"
                f"read: fleet/bus/GEM_UNDERSTAND.txt · fleet/bus/CB1_POWER_FIX.txt\n"
                f"loop_tick: epoch={epoch}\n"
            )
    elif "BUDDY ok" in prev and buddy_job:
        gem_reply = prev.rstrip() + f"\nloop_tick: {now} · epoch={epoch}\n"
    from_gem.parent.mkdir(parents=True, exist_ok=True)
    from_gem.write_text(gem_reply, encoding="utf-8")
    print(gem_reply)
    print(f"→ {from_gem}")

    exec_sh = STAN / "uncle_exec.sh"
    stay = STAN / "CB1_STAY_AWAKE.sh"
    if stay.is_file():
        subprocess.run(["bash", str(stay)], check=False)
    elif (bus / "lester/CB1_STAY_AWAKE.sh").is_file():
        subprocess.run(["bash", str(bus / "lester/CB1_STAY_AWAKE.sh")], check=False)
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
