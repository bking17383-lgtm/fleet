#!/usr/bin/env python3
"""CPT delegates to Uncle (CB1 STUDIO). Orders on bus — Uncle executes locally.

  python3 ~/.stan/cpt_delegate.py uncle aws_keys
  python3 ~/.stan/cpt_delegate.py uncle status
  python3 ~/.stan/cpt_delegate.py uncle "custom one-liner"

CPT does not SSH. Uncle reads orders · runs uncle_exec.sh · posts mac_outbox.
"""
from __future__ import annotations

import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, STAN

BUS = bus_root()
ORDERS = BUS / "fleet/orders/CB1_ORDERS.txt"
CONTROL = BUS / "fleet/bus/UNCLE_CONTROL.txt"
TO_UNCLE = BUS / "fleet/bus/cpt_to_uncle.txt"
FROM_UNCLE = BUS / "fleet/bus/uncle_to_cpt.txt"
ACK = BUS / "fleet/bus/cpt_ack_uncle.txt"
QUEUE = BUS / "fleet/bus/UNCLE_TASK_QUEUE.txt"

PRESETS: dict[str, list[str]] = {
    "aws_keys": [
        "Export lester keys.gdoc → lester/lester_keys.md on Drive (AKIA + secret line)",
        "OR drag convert_inbox jpg (20260615_192203 · 193522 · 193536) → CB1 Linux home",
        "bash ~/.stan/uncle_exec.sh",
        "Post uncle_to_cpt.txt: UNCLE clean — aws_keys — <ip> — <time>",
        "Read cpt_ack_uncle.txt — CPT heard you",
    ],
    "slave_boot": [
        "bash ~/.stan/slave_boot.sh",
        "python3 ~/.stan/local_slave.py STUDIO",
        "Post mac_outbox: UNCLE clean — slave_boot — <ip> — <time>",
    ],
    "status": [
        "python3 ~/.stan/local_slave.py STUDIO",
        "Post mac_outbox with mesh/sarah/desk health + Drive fuse state",
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _host() -> str:
    return socket.gethostname()


def delegate(preset_or_text: str) -> str:
    now = _now()
    host = _host()
    tasks = PRESETS.get(preset_or_text.lower())
    if tasks is None:
        tasks = [preset_or_text]

    header = (
        f"CB1 ORDERS — CPT DELEGATED · Uncle executes · not negotiates\n"
        f"Updated: {now}\n"
        f"From: CPT on {host}\n"
        f"Authority: fleet/CPT_DELEGATE_CONTRACT.txt · Brian word DELEGATE\n"
        f"\n"
        f"Uncle boot: bash ~/.stan/uncle_exec.sh  (or: python3 ~/.stan/cpt_delegate.py uncle status)\n"
        f"Word on CB1: STUDIO · Cursor only · GEM loads · does not captain\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"CPT ORDERS NOW ({len(tasks)} steps)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    body = "\n".join(f"  {i}. {t}" for i, t in enumerate(tasks, 1))
    footer = (
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"REPLY\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"Post fleet/bus/uncle_to_cpt.txt when done.\n"
        f"Read fleet/bus/cpt_ack_uncle.txt — CPT heard you.\n"
        f"Loop: fleet/CPT_UNCLE_LOOP.txt\n"
    )
    orders_text = header + body + footer
    ORDERS.parent.mkdir(parents=True, exist_ok=True)
    ORDERS.write_text(orders_text, encoding="utf-8")

    control = (
        f"UNCLE_CONTROL — {now}\n"
        f"mode=CPT_COMMANDS\n"
        f"preset={preset_or_text}\n"
        f"execute=bash ~/.stan/uncle_exec.sh\n"
        f"orders=fleet/orders/CB1_ORDERS.txt\n"
        f"read_cpt=fleet/bus/cpt_to_uncle.txt\n"
        f"write_uncle=fleet/bus/uncle_to_cpt.txt\n"
        f"read_ack=fleet/bus/cpt_ack_uncle.txt\n"
        f"law=fleet/CPT_UNCLE_LOOP.txt\n"
    )
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    CONTROL.write_text(control, encoding="utf-8")

    to_uncle = (
        f"--- CPT → UNCLE (TWO-WAY) ---\n"
        f"time: {now}\n"
        f"from: CPT {host}\n"
        f"order: {preset_or_text}\n"
        f"status: LOOP LIVE — CPT hears you now\n"
        f"run: bash ~/.stan/uncle_exec.sh\n"
        f"read: fleet/orders/CB1_ORDERS.txt\n"
        f"reply: fleet/bus/uncle_to_cpt.txt (Uncle writes ONLY here)\n"
        f"then read: fleet/bus/cpt_ack_uncle.txt\n"
        f"law: fleet/CPT_UNCLE_LOOP.txt\n"
        f"\n"
        f"Uncle was right: one-directional was wrong. Fixed.\n"
    )
    TO_UNCLE.parent.mkdir(parents=True, exist_ok=True)
    TO_UNCLE.write_text(to_uncle, encoding="utf-8")

    # Ack if Uncle already posted
    if FROM_UNCLE.is_file() and FROM_UNCLE.read_text(encoding="utf-8", errors="replace").strip():
        import subprocess
        subprocess.run([sys.executable, str(STAN / "cpt_uncle_sync.py")], check=False)

    line = f"[{now}] CPT delegated: {preset_or_text}\n"
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(line)

    # copy uncle_exec to bus lester path for CB1 pickup
    src_exec = STAN / "uncle_exec.sh"
    bus_exec = BUS / "lester/uncle_exec.sh"
    if src_exec.is_file():
        bus_exec.parent.mkdir(parents=True, exist_ok=True)
        bus_exec.write_text(src_exec.read_text(encoding="utf-8"), encoding="utf-8")

    return orders_text


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1].lower() != "uncle":
        print("Usage: cpt_delegate.py uncle <aws_keys|slave_boot|status|\"custom task\">")
        return 1
    text = " ".join(sys.argv[2:])
    out = delegate(text)
    print(out)
    print(f"\n→ {ORDERS}")
    print(f"→ {CONTROL}")
    print(f"→ {TO_UNCLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
