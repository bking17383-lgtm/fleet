#!/usr/bin/env python3
"""Bulk who's-who — one shot for plate.dev / CAPTN / no GUI."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
FLEET_BOARD = DRIVE / "lester/fleet_board.py"
OUT_MD = DRIVE / "fleet/WHO.md"
OUT_JSON = DRIVE / "fleet/WHO.json"

ENTRIES = [
    {
        "fleet_id": "cb1",
        "name": "Uncle / CB1",
        "callsign": "WRANGLER",
        "role": "Analyst · hardware protocols · budget",
        "network": "reload paused",
        "url": "",
        "notes": "Linux reload — fresh Uncle later",
    },
    {
        "fleet_id": "cb2",
        "name": "Daddy / CB2",
        "callsign": "BEACON",
        "role": "CAPTN desk · architect · Sarah host",
        "network": "Tailscale 100.115.92.26",
        "url": "http://127.0.0.1:8766/sarah",
        "notes": "Design desk — no Play traffic",
    },
    {
        "fleet_id": "puppy64",
        "name": "Puppy",
        "callsign": "PLATE",
        "role": "Network · art lane · 24/7 host",
        "network": "wlan0 192.168.1.4 · wg0 10.0.0.1",
        "url": "http://192.168.1.4:8765",
        "notes": "Chrome word PLATE · Cursor word PUPPY",
    },
    {
        "fleet_id": "phone-moto-lte",
        "name": "Moto Play",
        "callsign": "ROVER",
        "role": "Brian road phone · cellular",
        "network": "LTE",
        "url": "/rover on mesh",
        "notes": "fleet/ROVER_RADIO_URL.txt",
    },
    {
        "fleet_id": "phone-samsung-wifi",
        "name": "Samsung",
        "callsign": "TESTER",
        "role": "QA · Sarah trials",
        "network": "WiFi only",
        "url": "mesh home /",
        "notes": "No GL button trap — RADIO only",
    },
    {
        "fleet_id": "human-sarah",
        "name": "Sarah",
        "callsign": "—",
        "role": "Appointment tester · minimal intrusion",
        "network": "HTTPS or home WiFi",
        "url": "fleet/SARAH_SEND_WHEN_READY.txt",
        "notes": "Not fleet_id — human lane",
    },
    {
        "fleet_id": "human-brian",
        "name": "Brian",
        "callsign": "DADDY",
        "role": "Steer · art · inbox one-line",
        "network": "—",
        "url": "fleet/bus/BRIAN_INBOX.txt",
        "notes": "bking Gmail stays clean",
    },
]

SERVICES = [
    {"id": "mesh", "port": 8765, "host": "puppy64", "path": "mesh_radio.py"},
    {"id": "sarah", "port": 8766, "host": "cb2", "path": "/sarah"},
    {"id": "baseball", "port": 8002, "host": "puppy64", "path": "baseball"},
    {"id": "slicer", "port": 5000, "host": "puppy64", "path": "slicer"},
]


def refresh_fleet_available() -> str:
    if FLEET_BOARD.is_file():
        try:
            return subprocess.check_output(
                [sys.executable, str(FLEET_BOARD)], text=True, timeout=30
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
    p = DRIVE / "fleet/FLEET_AVAILABLE.txt"
    return p.read_text(encoding="utf-8") if p.is_file() else "(fleet_board not run)"


def main() -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    status_block = refresh_fleet_available()

    payload = {
        "updated": now,
        "entries": ENTRIES,
        "services": SERVICES,
        "status_raw": status_block,
        "refresh": "python3 MyDrive/lester/plate_who.py · domain: hitme.dev",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# WHO — fleet roster (bulk)",
        f"Updated: {now}",
        "",
        "Regenerate: `python3 lester/plate_who.py`",
        "",
        "| fleet_id | callsign | role | network | url |",
        "|----------|----------|------|---------|-----|",
    ]
    for e in ENTRIES:
        lines.append(
            f"| {e['fleet_id']} | {e['callsign']} | {e['role']} | {e['network']} | {e['url']} |"
        )
    lines.extend(["", "## Live status", "", "```", status_block.strip(), "```", ""])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD.name} + {OUT_JSON.name}")
    print(status_block)


if __name__ == "__main__":
    main()
