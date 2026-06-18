#!/usr/bin/env python3
"""Daddy delegate — orders only · nearly everything off the bus.

  python3 ~/.stan/daddy_delegate.py net mesh
  python3 ~/.stan/daddy_delegate.py studio loop
  python3 ~/.stan/daddy_delegate.py gem keys
  python3 ~/.stan/daddy_delegate.py buddy catalog
  python3 ~/.stan/daddy_delegate.py status

Writes fleet/bus/CPT_DELEGATE_NOW.txt — one queue Daddy reads in background.
Does NOT SSH · does NOT run uncle_exec on CB2.
"""
from __future__ import annotations

import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, STAN

BUS = bus_root()
NOW_FILE = BUS / "fleet/bus/CPT_DELEGATE_NOW.txt"
QUEUE = BUS / "fleet/bus/DADDY_DELEGATE_QUEUE.txt"

BOX_ALIASES = {"puppy": "net", "uncle": "studio", "net": "net", "studio": "studio"}

PRESETS: dict[str, dict[str, list[str]]] = {
    "net": {
        "mesh": [
            "Start mesh_radio on puppy :8765 · post health",
            "Run PUPPY_ONE_COMMAND.sh if stale",
            "Post fleet/bus/puppy_outbox.txt: NET clean — puppy64 — <ip> — <time>",
        ],
        "tunnel": [
            "Bring sarah.hitme.dev tunnel live on puppy",
            "Post PUBLIC_URL to fleet/bus/puppy_outbox.txt",
        ],
        "checkin": [
            "Say PUPPY in Cursor · run PUPPY_ONE_COMMAND.sh",
            "Post fleet/bus/puppy_outbox.txt: PUPPY CHECKIN — puppy64 — <ip> — <time>",
        ],
        "sarah": [
            "Ensure sarah voice :8766 health on puppy or tunnel path",
            "Post NET clean when services green",
        ],
    },
    "studio": {
        "loop": [
            "Say UNCLE on CB1 · Gem loads same box",
            "Run bash ~/.stan/uncle_exec.sh on CB1 Linux only (never penguin)",
            "Post fleet/bus/uncle_to_cpt.txt: UNCLE CHECKIN — cb1 — <ip> — <time>",
            "Read fleet/bus/cpt_ack_uncle.txt",
        ],
        "aws_keys": [
            "Export lester keys.gdoc → lester/lester_keys.md (AKIA + secret)",
            "Post uncle_to_cpt when done · never paste keys on bus",
        ],
        "gl_jailbreak": [
            "Read fleet/FIRST_PRIORITY.txt · GL_CONTROL_FIX · JAILBREAK_ANALYSIS",
            "With Gem: export free_lester_instructions.md · build scan_cheats.json on Drive",
            "Run bash ~/.stan/uncle_exec.sh on CB1 Linux only",
            "Post uncle_to_cpt: UNCLE CHECKIN — cb1 — <ip> — <time> · gl status",
        ],
        "fix_puppy": [
            "NOW: Daddy order · Uncle Linux lane only · read fleet/orders/CB1_ORDERS.txt",
            "LAN scan puppy64 (192.168.1.4): curl :8002 :8765 :8766 · ping · post honest results",
            "Write fleet/bus/cpt_to_puppy.txt — keyboard one-liner if remote exec blocked",
            "Update fleet/bus/puppy_needs.txt with scan + blockers · no SSH if refused",
            "Gem lane got separate inbox: fleet/bus/cpt_to_gem.txt (Drive scripts · not your delegate)",
            "Post uncle_to_cpt: UNCLE CHECKIN — cb1 — <ip> — <time> · puppy=<fixed|blocked|needs_keyboard>",
            "Read cpt_ack_uncle.txt — Daddy hears you",
        ],
    },
    "gem": {
        "keys": [
            "Export lester keys.gdoc → lester/lester_keys.md on Drive",
            "Post fleet/bus/gem_to_cpt.txt: GEM ok — keys exported — <time>",
            "Write fleet/bus/GEM_UNDERSTAND.txt honest gaps",
        ],
        "catalog": [
            "Read fleet/STUCK_BOARD.txt",
            "Update fleet/bus/GEMINI_DRIVE_REPORT.txt",
            "Post gem_to_cpt when done",
        ],
        "loop": [
            "Read fleet/bus/cpt_to_gem.txt",
            "Run python3 ~/GoogleDrive/MyDrive/lester/gem_loop_bridge.py on CB1",
            "Post gem_to_cpt.txt",
        ],
    },
    "buddy": {
        "catalog": [
            "Read fleet/bus/BUDDY_INBOX.txt",
            "Catalog stuck items on Drive · update GEMINI_DRIVE_REPORT.txt",
            "Post gem_to_cpt ack",
        ],
        "drive": [
            "Drive pass — BRIAN_LAW_AUTO · stuck gaps only",
            "No captain · loader hands",
        ],
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _host() -> str:
    return socket.gethostname()


def _orders_path(box: str) -> Path:
    return {
        "net": BUS / "fleet/bus/cpt_to_puppy.txt",
        "studio": BUS / "fleet/bus/cpt_to_uncle.txt",
        "gem": BUS / "fleet/bus/cpt_to_gem.txt",
        "buddy": BUS / "fleet/bus/BUDDY_INBOX.txt",
    }.get(box, BUS / "fleet/bus/cpt_to_uncle.txt")


def delegate(box: str, preset: str) -> str:
    box = BOX_ALIASES.get(box.lower(), box.lower())
    preset = preset.lower()

    if box == "studio" and preset == "loop":
        try:
            r = subprocess.run(
                [sys.executable, str(STAN / "cpt_gem_loop.py"), "listen"],
                capture_output=True,
                timeout=20,
                text=True,
            )
            ack = (BUS / "fleet/bus/cpt_ack_gem.txt").read_text(encoding="utf-8", errors="replace")
            if "loop: LIVE" in ack and "uncle_heard: YES · CB1" in ack:
                subprocess.run([sys.executable, str(STAN / "cpt_gem_loop.py"), "ping"], check=False)
                return "SKIP delegate studio/loop — Uncle+Gem already LINKED on cb1\n"
        except (OSError, subprocess.SubprocessError):
            pass

    tasks = PRESETS.get(box, {}).get(preset)
    if tasks is None:
        tasks = [preset.replace("_", " ")]

    now = _now()
    host = _host()

    if box == "studio":
        subprocess.run(
            [sys.executable, str(STAN / "cpt_delegate.py"), "uncle", preset if preset in PRESETS.get("studio", {}) else preset],
            check=False,
        )

    header = (
        f"--- CPT DELEGATE — {box.upper()} · {preset} ---\n"
        f"time: {now}\n"
        f"from: Daddy/CPT on {host} (CB2)\n"
        f"mode: ORDERS ONLY · execute on target box · not on penguin\n"
        f"law: fleet/DADDY_BACKGROUND.txt · fleet/CPT_DELEGATE_CONTRACT.txt\n"
        f"\n"
    )
    body = "\n".join(f"  {i}. {t}" for i, t in enumerate(tasks, 1))
    footer = (
        f"\n\nReply on bus when done. Daddy stays in background.\n"
        f"Word: DELEGATE · NOW HERE overrides once\n"
    )
    order_text = header + body + footer

    target = _orders_path(box)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(order_text, encoding="utf-8")

    queue_line = f"[{now}] {box}/{preset}\n"
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(queue_line)

    now_block = (
        f"CPT DELEGATE NOW — {now}\n"
        f"host={host} · default=delegate · Daddy in background\n"
        f"\n"
        f"LAST: {box}/{preset}\n"
        f"orders → {target.relative_to(BUS) if str(target).startswith(str(BUS)) else target.name}\n"
        f"\n"
        f"TASKS\n{body}\n"
        f"\n"
        f"BOX LAW\n"
        f"  net → puppy executes mesh/tunnel\n"
        f"  studio → CB1 uncle_exec only (never penguin)\n"
        f"  gem/buddy → Chrome Drive hands\n"
        f"  cpt → captain + screen + autopilot only\n"
    )
    NOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOW_FILE.write_text(now_block, encoding="utf-8")
    return order_text


def status() -> str:
    now = _now()
    host = _host()
    screen = safe_read(BUS / "fleet/bus/DADDY_SCREEN.txt")
    ready = safe_read(BUS / "fleet/bus/CPT_READY.txt")
    lines = [
        f"DADDY STATUS — {now}",
        f"host={host} · mode=background · delegate default",
        "",
        "SCREEN (tail)",
        *(screen.splitlines()[-6:] if screen else ["(no capture yet)"]),
        "",
        "READY (tail)",
        *(ready.splitlines()[:12] if ready else ["(run cpt_autopilot once)"]),
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    return text


def safe_read(p: Path) -> str:
    try:
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    return ""


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1].lower() == "status":
        status()
        return 0
    if len(sys.argv) < 3:
        print("Usage: daddy_delegate.py <net|studio|gem|buddy> <preset> | status")
        return 1
    out = delegate(sys.argv[1], " ".join(sys.argv[2:]))
    print(out)
    print(f"\n→ {_orders_path(sys.argv[1].lower())}")
    print(f"→ {NOW_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
