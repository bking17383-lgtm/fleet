#!/usr/bin/env python3
"""One-shot identity repair — sync law · honest acks · Gem orders on Drive."""
from __future__ import annotations

import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STAN = Path.home() / ".stan"
LOCAL = STAN / "fleet_bus"
DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _cp(src: Path, dst: Path) -> bool:
    if not src.is_file():
        print(f"SKIP missing {src}")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"→ {dst}")
    return True


def main() -> int:
    if not (DRIVE / "fleet").is_dir():
        print("Drive not mounted — fix fuse first", file=sys.stderr)
        return 1

    now = _now()
    host = socket.gethostname()

    # Sync law + Gem self-fix + bridge to Drive (CB1 pickup)
    _cp(LOCAL / "fleet/NAMING_LAW.txt", DRIVE / "fleet/NAMING_LAW.txt")
    _cp(LOCAL / "drop_pile/to_gemini/GEM_SELF_FIX.txt", DRIVE / "drop_pile/to_gemini/GEM_SELF_FIX.txt")
    _cp(LOCAL / "lester/GEM_SELF_FIX.txt", DRIVE / "lester/GEM_SELF_FIX.txt")
    _cp(STAN / "gem_loop_bridge.py", DRIVE / "lester/gem_loop_bridge.py")
    _cp(STAN / "bus_lane_guard.py", DRIVE / "lester/bus_lane_guard.py")

    # Clear poison — waiting state (Uncle/Gem must repost from CB1)
    uncle_wait = f"""WAITING — Uncle must repost from CB1 Linux · {now}
Gem: read drop_pile/to_gemini/GEM_SELF_FIX.txt
Run: bash ~/.stan/uncle_exec.sh
Line: UNCLE CHECKIN — cb1 — <ip> — <time>
"""
    gem_wait = f"""WAITING — Gem must repost from CB1 · {now}
Read: fleet/NAMING_LAW.txt · lester/GEM_SELF_FIX.txt
Run on CB1 Linux: python3 ~/GoogleDrive/MyDrive/lester/gem_loop_bridge.py
Line: GEM ok — cb1 — <ip> — {now}
"""
    (DRIVE / "fleet/bus/uncle_to_cpt.txt").write_text(uncle_wait, encoding="utf-8")
    (DRIVE / "fleet/bus/gem_to_cpt.txt").write_text(gem_wait, encoding="utf-8")
    print("→ cleared uncle_to_cpt · gem_to_cpt waiting state")

    cpt_to_gem = f"""--- Daddy → Gem (FIX NOW) ---
time: {now}
from: Daddy on {host} (penguin · captain)

Gem — you are NOT Daddy. Read these FIRST:
  fleet/NAMING_LAW.txt
  drop_pile/to_gemini/GEM_SELF_FIX.txt

DO NOW on Uncle's box (CB1 · never penguin):
  1. python3 ~/GoogleDrive/MyDrive/lester/gem_loop_bridge.py
  2. Write fleet/bus/gem_to_cpt.txt — host must be cb1
  3. Uncle writes fleet/bus/uncle_to_cpt.txt — UNCLE CHECKIN — cb1 — <ip> — <time>

Reply here when done. Do NOT run uncle_exec on penguin.

Word: GEM
"""
    (DRIVE / "fleet/bus/cpt_to_gem.txt").write_text(cpt_to_gem, encoding="utf-8")

    cpt_to_uncle = f"""--- Daddy → Uncle ---
time: {now}
from: Daddy on {host}

Uncle — CB1 Linux only. Never penguin.
run: bash ~/.stan/uncle_exec.sh
reply: fleet/bus/uncle_to_cpt.txt
read: fleet/bus/cpt_ack_uncle.txt · drop_pile/to_gemini/GEM_SELF_FIX.txt

UNCLE CHECKIN — cb1 — <ip> — <time>
"""
    (DRIVE / "fleet/bus/cpt_to_uncle.txt").write_text(cpt_to_uncle, encoding="utf-8")

    # Correct Gem's wrong self-notes on Drive
    learned = DRIVE / "drop_pile/from_cursor/gem_position_learned.md"
    learned.parent.mkdir(parents=True, exist_ok=True)
    learned.write_text(
        f"""# Gem position — CORRECTED by Daddy

**Time:** {now}
**From:** Daddy (penguin)
**Supersedes:** gem_position_learned.md poison

## Truth

| Word | Box | Shell |
|------|-----|-------|
| Daddy | CB2 | penguin — captain only |
| Uncle | CB1 | cb1 Linux — execute |
| Gem | CB1 | Chrome loader — same box as Uncle, different hat |
| Puppy | puppy64 | NET |

## Gem's mistake (fixed)

Gem ran from **penguin Cursor** and posted `uncle_to_cpt` / `gem_to_cpt` claiming TWO_WAY.
That poisoned Uncle's identity. Those posts are INVALIDATED.

## Gem fix (CB1 only)

Read `drop_pile/to_gemini/GEM_SELF_FIX.txt` · run `lester/gem_loop_bridge.py` on CB1 Linux.

## Keys

Still CLOSED until `lester/lester_keys.md` has real AKIA lines.
""",
        encoding="utf-8",
    )

    # Loop ping + honest acks
    for cmd in (
        [sys.executable, str(STAN / "cpt_gem_loop.py"), "ping"],
        [sys.executable, str(STAN / "cpt_gem_loop.py"), "listen"],
        [sys.executable, str(STAN / "cpt_uncle_sync.py")],
        [sys.executable, str(STAN / "fleet_checkin.py")],
        [sys.executable, str(STAN / "daddy_delegate.py"), "status"],
    ):
        subprocess.run(cmd, check=False)

    print(f"\nDONE {now} · Gem read GEM_SELF_FIX on CB1 · word: GEM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
