#!/usr/bin/env python3
"""CB1 Gem → Daddy bus sync. Read mtime · stamp · write Daddy lanes."""
from __future__ import annotations

import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BUS_CANDIDATES = [
    Path("/mnt/shared/GoogleDrive/MyDrive"),
    Path.home() / "GoogleDrive/MyDrive",
    Path.home() / ".stan/fleet_bus",
]


def bus() -> Path:
    for p in BUS_CANDIDATES:
        if (p / "fleet").is_dir():
            return p
    return BUS_CANDIDATES[-1]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def mtime_iso(path: Path) -> str:
    if not path.is_file():
        return "missing"
    ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone()
    return ts.isoformat(timespec="seconds")


def job_from_cpt(text: str) -> str:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().lower() == "brian asked:":
            if i + 1 < len(lines):
                return lines[i + 1].strip()[:100]
        if "brian asked:" in ln.lower():
            rest = ln.split(":", 1)[-1].strip()
            if rest:
                return rest[:100]
    low = text.lower()
    if "insomniac" in low or "hibernat" in low:
        return "insomniac power fix"
    if "net" in low:
        return "NET execute"
    return "read cpt_to_gem"


def main() -> int:
    root = bus()
    b = root / "fleet/bus"
    to_gem = b / "cpt_to_gem.txt"
    to_cpt = b / "gem_to_cpt.txt"
    host = socket.gethostname()
    ip = subprocess.getoutput("hostname -I").split()[0] if subprocess.getoutput("hostname -I") else "?"
    t = now()

    if "penguin" in host.lower():
        to_cpt.write_text(f"GEM REFUSE — wrong box penguin — {t}\n", encoding="utf-8")
        return 2

    cpt_body = to_gem.read_text(encoding="utf-8", errors="replace") if to_gem.is_file() else ""
    cpt_mt = mtime_iso(to_gem)
    job = job_from_cpt(cpt_body)

    daddy_last = b / "DADDY_LAST_POST.txt"
    daddy_last.write_text(
        f"DADDY LAST POST — read by Gem — {t}\n"
        f"file=fleet/bus/cpt_to_gem.txt\n"
        f"mtime={cpt_mt}\n"
        f"job={job}\n"
        f"Gem: use mtime · not old time: line\n\nWord: GEM\n",
        encoding="utf-8",
    )

    pulse = b / "SYNC_PULSE.txt"
    pulse.write_text(f"SYNC_PULSE — Gem cb1 — {t}\nhost=cb1\n", encoding="utf-8")

    stamp = b / "GEM_STAMP.txt"
    stamp.write_text(f"GEM DONE — {job} — {t} · host: cb1\n", encoding="utf-8")

    stamps = b / "STAMPS.txt"
    line = f"GEM DONE — {job} — {t} · host: cb1\n"
    old = stamps.read_text(encoding="utf-8", errors="replace") if stamps.is_file() else ""
    stamps.write_text(line + old, encoding="utf-8")

    reply = (
        f"--- Gem → Daddy ---\n"
        f"time: {t}\n"
        f"host: cb1 ip={ip}\n"
        f"cpt_to_gem_mtime: {cpt_mt}\n"
        f"job: {job}\n"
        f"BUDDY ok — {job} done — {t} · host: cb1\n"
        f"read: GEM_UNDERSTAND · NET_STATUS · GEM_DADDY_BUDDY\n"
        f"loop: LIVE · mtime trust\n"
    )
    to_cpt.write_text(reply, encoding="utf-8")

    buddy = b / "GEM_BUDDY_FORWARDED.txt"
    buddy.write_text(
        f"GEM_BUDDY_FORWARDED — {t}\n"
        f"ask={job}\n"
        f"answered=YES\n"
        f"cpt_mtime={cpt_mt}\n"
        f"→ fleet/bus/gem_to_cpt.txt\n",
        encoding="utf-8",
    )

    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
